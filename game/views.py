from django.shortcuts import  render, redirect
from .forms import RegisterUserForm, NumberInputForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Game


def register(request):
	if request.user.is_authenticated:
		return redirect('main_page_url')
	if request.method == "POST":
		form = RegisterUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect("main_page_url")
		return render(request, 'registration/register.html', context={"register_form":form})
	form = RegisterUserForm()
	return render(request=request, template_name="registration/register.html", context={"register_form":form})


@login_required(login_url='/login/')
def main_page(request):
	user = request.user
	active_game = user.games.filter(game_ended=False).last()
	if active_game and active_game.users.all().count() == 2:
		return redirect('game_page_url')
	if active_game:
		active_game.delete()
	return render(request, 'game/main.html')


@login_required(login_url='/login/')
def game_page(request):
	user = request.user
	active_game = user.games.filter(game_ended=False).last()
	if not active_game:
		return redirect('main_page_url')

	if active_game.users.all().count() != 2:
		active_game.delete()
		return redirect('main_page_url')

	if request.method == 'GET':
		form = NumberInputForm()
		enemy = active_game.users.all().exclude(pk=user.pk).first()
		context = {
			'game': active_game,
			'enemy': enemy,
			'number_form': form,
		}
		return render(request, 'game/game_page.html', context=context)


@login_required(login_url='/login/')
def history(request):
	user = request.user
	if request.method == 'GET':
		context = {
			'games': Game.get_history_for_user(user.pk)
		}
		return render(request, 'game/games_history.html', context=context)
