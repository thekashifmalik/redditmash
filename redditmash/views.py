from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from redditmash.models import Post, StatsReddit, Stats, Choice
import hashlib

def index(request):
	# POST request
	# ------------------------------------------------
	if request.is_ajax() and request.method == 'POST':
		# Check if the choice is stale
		try:
			choice = Choice.objects.get(id = request.session['last_sent_choice_id'])
			# Send decision
			process_decision.delay(request.POST['winner_id'], choice.id)
		except Choice.DoesNotExist:
			# Choice is stale - Do nothing
			pass
		# redirect to index for next choice
		HttpResponseRedirect(reverse('redditmash.views.index'))

	# GET request
	# ------------------------------------------------
	# Get or create choices sent session variable
	if not request.session.get('choices_sent', None):
		request.session['choices_sent'] = []

	# Get ordered list of available choices
	choices_active = Choice.objects.filter(is_active=True).order_by('-times_completed')
	
	# If there are no available choices render error page
	if not choices_active:
		return render_to_response('index_no_data.html', context_instance=RequestContext(request))

	# Default case - least active page
	least_active_idx = len(choices_active) - 1
	choice_to_use = choices_active[least_active_idx]

	# Get most active choice for chance of chat overlap
	for c in choices_active:
		if c.id not in request.session['choices_sent']:
			choice_to_use = c
			break
	# TODO Send template variables
	request.session['choices_sent'].append(choice_to_use.id)
	request.session.modified = True
	return render_to_response('index.html', context_instance=RequestContext(request))

def rankings(request):
	posts = Post.objects.filter(is_active=True).order_by('stats__rank')[:25]
	posts_send = []
	for p in posts:
		posts_send.append({
			'title': p.title,
			'data-value': hashlib.md5(p.title).hexdigest()[:7],
			'url': p.url,
		})

	reddit_posts = Post.objects.filter(is_active_reddit=True).order_by('statsreddit__rank')[:25]
	reddit_posts_send = []
	for p in reddit_posts:
		reddit_posts_send.append({
			'title': p.title,
			'data-value': hashlib.md5(p.title).hexdigest()[:7],
			'url': p.url,
		})
	return render_to_response('rankings.html', {'posts': posts_send, 'reddit_posts': reddit_posts_send}, context_instance=RequestContext(request))