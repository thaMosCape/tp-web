from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, update_session_auth_hash, login as log_in, logout as log_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from .models import Question, Tag, AnswerForm, Answer, UserForm, Profile, ProfileForm
from .forms import LoginForm, PasswordUpdateForm, SignupForm


context = {
  'toptags' : [" "] * 20,
  'topusers' : [" "] * 10,
}

def index(request):
    questions = Question.objects.recent()
    context['questions'] = paginate(questions, request, 20)
    for q in context['questions']: q.taglist = q.tags.all()
    context['header'] = 'index'
    return render(request, './index.html', context)

def hot(request):
    questions = Question.objects.hot()
    context['questions'] =  paginate(questions, request, 20)
    for q in context['questions']: q.taglist = q.tags.all()
    context['header'] = 'hot'
    return render(request, './index.html', context)

def tag(request, tag):
    questions = get_object_or_404(Tag, pk=tag).question_set.all()
    context['questions'] = paginate(questions, request, 20)
    for q in context['questions']: q.taglist = q.tags.all()
    context['tag'] = tag
    context['header'] = 'tag'
    return render(request, './index.html', context)

def question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('%s?continue=%s' % (settings.LOGIN_URL, request.path))
        answer = Answer(question=question, author=request.user.profile, rating=0, is_correct=False)
        form = AnswerForm(request.POST, instance=answer)
        form.save()
    context['form'] = AnswerForm()
    question.taglist = question.tags.all()
    answers = question.answer_set.all()
    context['answers'] = paginate(answers, request, 30)
    context['question'] = question
    return render(request, './question.html', context)

def login(request):
    log_out(request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
          user = authenticate(username=form.cleaned_data['username'], 
                              password=form.cleaned_data['password'])
          if user is not None:
              log_in(request, user)
              url  = request.POST.get('continue') if request.POST.get('continue') else 'index'
              return redirect(url)
          else:
              form.non_field_errors = 'Wrong credentials'
    else:
        form = LoginForm()
    context['form'] = form
    context['location'] = request.GET.get('continue') if request.GET.get('continue') else 'index'
    return render(request, './login.html', context)

def logout(request):
    log_out(request)
    return redirect('index')

def signup(request):
    if request.user.is_authenticated:
        log_out(request)
        return redirect('signup')
    if request.method == 'POST':
        context['form'] = SignupForm(request.POST, request.FILES)
        if context['form'].is_valid():
            user = User.objects.create_user(context['form'].cleaned_data['username'], 
                                    context['form'].cleaned_data['email'], 
                                    context['form'].cleaned_data['password'])
            Profile.objects.create(user=user, rating=0, avatar=File(request.FILES['avatar']))
            return redirect('index')
    else:
        context['form'] = SignupForm()
    return render(request, './signup.html', context)

@login_required(redirect_field_name='continue')
def ask(request):
    return render(request, './ask.html', context)

@login_required(redirect_field_name='continue')
def settings(request):
    if request.method == 'POST':
        context['userform'] = UserForm(request.POST, instance=request.user)
        context['profileform'] = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        user = context['userform'].save(commit=False)
        context['passupdateform'] = PasswordUpdateForm(request.POST)
        if authenticate(username=request.user.username, password=user.password) is None:
            context['userform'].non_field_errors = 'Authentication error'
        else:
            if context['passupdateform'].is_valid() and context['passupdateform'].cleaned_data['origin'] != '':
                user.password = make_password(context['passupdateform'].cleaned_data['origin'])
            user.save()
            update_session_auth_hash(request, user)
            context['profileform'].save()
    elif request.method == 'GET':
        context['userform'] = UserForm(initial={
          'username' : request.user.username,
          'email' : request.user.email,
        })
        context['profileform'] = ProfileForm(initial={'avatar' : request.user.profile.avatar})
        context['passupdateform'] = PasswordUpdateForm()
    return render(request, './settings.html', context)

def paginate(objects_list, request, page_size):
    paginator = Paginator(objects_list, page_size)
    page = request.GET.get('page') if request.GET.get('page') else 1
    try:
        objects = paginator.page(page)
    except:
        objects = paginator.page(1)
    return objects
