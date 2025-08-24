from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

# def login_view(request):
#     if request.user.is_authenticated:
#         logger.debug(f"User {request.user.username} already authenticated, redirecting to employee_list")
#         return redirect('employee_list')
    
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         if not username or not password:
#             logger.warning("Missing username or password in login attempt")
#             return JsonResponse({
#                 'error': 'Veuillez fournir un nom d’utilisateur et un mot de passe.'
#             }, status=400)
        
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             logger.info(f"User {username} logged in successfully")
#             request.session['test_key'] = 'test_value'
#             request.session.modified = True
#             logger.debug(f"Session set: {request.session.get('test_key')}")
#             return JsonResponse({'success': True}, status=200)
#         else:
#             logger.warning(f"Failed login attempt for username={username}")
#             return JsonResponse({
#                 'error': 'Nom d’utilisateur ou mot de passe incorrect.'
#             }, status=401)
    
#     return render(request, 'authentication/login.html')

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'employee_list'

    if request.user.is_authenticated:
        logger.debug(f"User {request.user.username} already authenticated, redirecting to {next_url}")
        return redirect(next_url)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            logger.warning("Missing username or password in login attempt")
            return JsonResponse({
                'error': 'Veuillez fournir un nom d’utilisateur et un mot de passe.'
            }, status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully")
            request.session['test_key'] = 'test_value'
            request.session.modified = True

            # Validate the redirect target for safety
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = 'employee_list'  # fallback to safe default

            logger.debug(f"Redirecting to: {next_url}")
            return JsonResponse({'success': True, 'redirect_url': next_url}, status=200)
        else:
            logger.warning(f"Failed login attempt for username={username}")
            return JsonResponse({
                'error': 'Nom d’utilisateur ou mot de passe incorrect.'
            }, status=401)

    return render(request, 'authentication/login.html', {'next': next_url})

@login_required
def logout_view(request):
    logger.info(f"User {request.user.username} logged out")
    logout(request)
    return redirect('login')
@login_required
def logout_view(request):
    logger.info(f"User {request.user.username} logged out")
    logout(request)
    return redirect('login')

def index_view(request):
    # This is a placeholder for the index view logic
    return render(request, 'main/index.html')

