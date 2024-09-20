from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from allauth.account.forms import LoginForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import Response, ConfirmationCode
from .forms import ResponseForm
import logging
from .forms import AdvertisementForm
from .models import Advertisement, Profile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from allauth.account.views import SignupView
from django.contrib import messages
from django.shortcuts import redirect

from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def home(request):
    advertisements = Advertisement.objects.all().order_by('-created_at')[:10]
    context = {'advertisements': advertisements}
    return render(request, 'home.html', context)


@login_required
def profile(request):
    user_ads = Advertisement.objects.filter(user=request.user)
    responses = Response.objects.filter(advertisement__in=user_ads)
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.subscribe_to_news = request.POST.get('subscribe_to_news') == 'on'
        profile.save()

    context = {
        'user_ads': user_ads,
        'responses': responses,
        'profile': profile,
        'user': request.user,  # Передаем  'user'  в  контекст
    }
    return render(request, 'profile.html', context)


def custom_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Деактивируем пользователя до подтверждения email
            user.save()

            # Генерация кода подтверждения
            confirmation_code = ConfirmationCode.objects.create(user=user)

            current_site = get_current_site(request)
            mail_subject = 'Активируйте ваш аккаунт.'
            message = render_to_string('account/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': confirmation_code.code,
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            messages.success(request, 'Пожалуйста, подтвердите адрес электронной почты, чтобы завершить регистрацию.')
            return redirect('home')  # Перенаправляем на страницу успешной регистрации


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and ConfirmationCode.objects.filter(user=user, code=token).exists():
        user.is_active = True
        user.save()
        ConfirmationCode.objects.filter(user=user).delete()  # Удаляем код подтверждения
        login(request, user)  # Авторизуем пользователя
        messages.success(request,
                         'Спасибо за подтверждение адреса электронной почты. Теперь вы можете войти в свой аккаунт.')
        return redirect('home')  # Перенаправляем на главную страницу
    else:
        messages.error(request, 'Ссылка активации недействительна!')
        return redirect('home')


def advertisement_list(request):
    category = request.GET.get('category')
    if category:
        advertisements = Advertisement.objects.filter(category=category)
    else:
        advertisements = Advertisement.objects.all()

    paginator = Paginator(advertisements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'advertisement_list.html', {
        'page_obj': page_obj,
        'category': category,
        'category_choices': Advertisement.CATEGORY_CHOICES
    })


@login_required
def advertisement_detail(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)

    # Фильтруем отклики, чтобы показывать только принятые
    responses = advertisement.responses.filter(accepted=True)

    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.advertisement = advertisement
            response.user = request.user
            response.save()
            messages.success(request, 'Ваш отклик отправлен.')
            return redirect('advertisement_detail', pk=advertisement.pk)
    else:
        form = ResponseForm()

    context = {
        'advertisement': advertisement,
        'responses': responses,
        'form': form  # Передаем форму для создания откликов
    }
    return render(request, 'advertisement_detail.html', context)


@login_required
def advertisement_create(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.user = request.user
            advertisement.save()
            return redirect('advertisement_detail', pk=advertisement.pk)
    else:
        form = AdvertisementForm()
    return render(request, 'advertisement_form.html', {'form': form})


@login_required
def response_create(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.advertisement = advertisement
            response.user = request.user
            response.save()

            send_mail(
                'Новый отклик на ваше объявление',
                f'На ваше объявление "{response.advertisement.title}" поступил новый отклик.\n\n{response.text[:100] if len(response.text) > 100 else response.text}',
                settings.DEFAULT_FROM_EMAIL,  # Замените на ваш email
                [response.advertisement.user.email],
                fail_silently=False,
            )

            return redirect('advertisement_detail', pk=advertisement.pk)
    else:
        form = ResponseForm()
    return render(request, 'response_form.html', {'form': form, 'advertisement': advertisement})


@login_required
def user_responses(request):
    my_user_responses = Response.objects.filter(advertisement__user=request.user)
    return render(request, 'user_responses.html', {'user_responses': my_user_responses})


@login_required
def accept_response(request, pk):
    response = get_object_or_404(Response, pk=pk)
    if request.user == response.advertisement.user:
        response.accepted = True
        response.save()
        # Отправляем уведомление пользователю, оставившему отклик
        send_mail(
            'Ваш отклик принят!',
            f'Ваш отклик на объявление "{response.advertisement.title}" был принят.',
            settings.DEFAULT_FROM_EMAIL,  # Замените на ваш email
            [response.user.email],
            fail_silently=False,
        )
        messages.success(request, 'Отклик принят.')
    else:
        messages.error(request, 'У вас нет прав для выполнения этого действия.')
    return redirect('advertisement_detail', pk=response.advertisement.pk)


@login_required
def delete_response(request, pk):
    response = get_object_or_404(Response, pk=pk)
    if request.user == response.advertisement.user or request.user == response.user:
        response.delete()
        messages.success(request, 'Отклик удален.')
    else:
        messages.error(request, 'У вас нет прав для выполнения этого действия.')
    return redirect('advertisement_detail', pk=response.advertisement.pk)


@login_required
def user_responses(request):
    user_ads = Advertisement.objects.filter(user=request.user)
    responses = Response.objects.filter(advertisement__in=user_ads)
    context = {
        'responses': responses,
        'user_ads': user_ads  # Передаем объявления пользователя в контекст
    }
    return render(request, 'user_responses.html', context)


def custom_login(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            # Убедитесь, что используете правильное имя поля
            username = login_form.cleaned_data.get('username')  # Используйте .get() для избежания KeyError
            password = login_form.cleaned_data.get('password')
            if username and password:  # Проверка, что оба поля заполнены
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Вы успешно вошли в систему.')
                    return redirect('mrpg')
                else:
                    messages.error(request, 'Неверное имя пользователя или пароль.')
            else:
                messages.error(request, 'Необходимо заполнить все поля.')
    else:
        login_form = LoginForm()

    return render(request, 'login.html', {'login_form': login_form})


class MySignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Письмо с подтверждением отправлено на вашу почту.')
        return redirect('account_email_verification_sent')


@login_required
def advertisement_edit(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)
    if request.user != advertisement.user:
        return redirect('advertisement_detail', pk=pk)
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES, instance=advertisement)
        if form.is_valid():
            form.save()
            return redirect('advertisement_detail', pk=pk)
    else:
        form = AdvertisementForm(instance=advertisement)
    return render(request, 'advertisement_edit.html', {'form': form})


signup = MySignupView.as_view()
