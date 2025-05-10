from Orders.models import Order
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .forms import MessageForm
from Home.models import UserProfile
from .models import Message
from django.http import JsonResponse
import datetime



def Userchat(request, order_id, username):
    # Getting the user and order objects based on the given IDs
    user = get_object_or_404(User, username=username)
    order = get_object_or_404(Order, id=order_id)
    form = MessageForm()
    current_user = request.user
    if username == current_user.username:
        pass
    else:
        return HttpResponseForbidden("Access Denied")

    if user == order.seller:
        receiver = order.buyer
    else:
        receiver = order.seller


    reciver_profile = UserProfile.objects.filter(user=receiver)
    sender_profile = UserProfile.objects.filter(user=user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            # Saving the message object
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.service = order.service
            message.order = order
            message.save()
            messages = Message.objects.filter(order=order)

            return redirect('userchat', order.id, request.user)

    messages = Message.objects.filter(order=order)

    context = {
        'order': order,
        'user': user,
        'form': form,
        'receiver': receiver,
        'messages': messages,
        'reciver_profile': reciver_profile,
        'sender_profile': sender_profile
    }
   
    return render(request, 'Userchat.html', context)


def get_messages(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    messages = Message.objects.filter(order=order)
    message_data = []

    for message in messages:
        timestamp = datetime.datetime.now()
        formatted_timestamp =  message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if request.user == message.sender:
            message_data.append(f"<p class='message sender'><span class='username'>{formatted_timestamp}</span><br>{message.message}</p>")
        else:
            message_data.append(f"<p class='message receiver'><span class='username'>{formatted_timestamp}</span> <br> {message.message}</p>")

    # Returning JSON response containing formatted message data
    return JsonResponse({"messages": "\n".join(message_data)})
