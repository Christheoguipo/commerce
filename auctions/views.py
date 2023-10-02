from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms
from decimal import Decimal

from . models import *


def index(request, category=None):

    listings = Listing.objects.filter(active=True)

    if category:
        categories = Category.objects.get(name=category)
        filtered_listing = listings.filter(category=categories)
        return render(request, "auctions/index.html", {
            "listings": filtered_listing
        })
    else:
        return render(request, "auctions/index.html", {
            "listings": listings
        })


def categories(request):
    categories = Category.objects.all()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)

            next_url = request.POST.get('next')
            
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

@login_required
def create_listing(request):

    if request.method == "POST":
        form = ListingForm(request.POST)

        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            image_url = form.cleaned_data["image_url"]
            price =  Decimal(form.cleaned_data["price"])
            category = form.cleaned_data["category"]
            user = request.user

            new_listing = Listing(title=title,description=description,url=image_url,price=price,category=category,user=user)
            new_listing.save()
 
            messages.success(request, "Successfully saved!")
            
            return redirect("create-listing")
    
    return render(request, "auctions/create-listing.html", {
            "form": ListingForm() 
        })


@login_required
def watchlist(request):
    
    watchlist = Watchlist.objects.filter(user=request.user)

    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
    })


def listing(request, id):
    
    listing = Listing.objects.get(id=id)
    comments = Comment.objects.filter(listing=listing)
    form = None
    isWatchlist = None
    seller = listing.user
 
    has_bid = False
    # Check if the listing has a bidder 
    if listing.highest_bidder:
        has_bid = True

    # Use "request.user.id" instead of just "request.user" to avoid SimpleLazyObject errors when user is not logged in
    if request.user.id is not None:
        # Check if the listing is in the user's Watchlist
        isWatchlist = Watchlist.objects.filter(listing=listing, user=request.user).exists()

    if request.method == "POST":
        form_name = request.POST["form_name"]
        if form_name == "watchlist_form":

            if isWatchlist:
                watchlist_item = Watchlist.objects.filter(listing=listing)
                watchlist_item.delete()
            
            else:  
                new_watchlist_item = Watchlist(listing=listing, user=request.user)
                new_watchlist_item.save()

            # Redirect to the same page after the POST request to refresh the content
            return redirect("listing", id=id)

        if form_name == "bid_form":
            form = BiddingForm(request.POST)
            
            if form.is_valid():
                bid_amount = form.cleaned_data["bid_amount"]
                user = request.user
                bid = Bid(amount=bid_amount,listing=listing,user=user)
                bid.save()
 
                messages.success(request, "Bid placed.")

                return redirect("listing", id=id)

        if form_name == "close_bid_form":
            
            listing.active = False
            listing.save()

            messages.success(request, "Bid closed.")
            return redirect("listing", id=id)

        if form_name == "comment_form":
            comment_form = CommentForm(request.POST)
            
            if comment_form.is_valid():
                text = comment_form.cleaned_data["text"]
                user = request.user
                comment = Comment(text=text, listing=listing, user=user)
                comment.save()

                messages.success(request, "Comment posted.")
                return redirect("listing", id=id)
   
    else:
        form = BiddingForm(initial={"listing_price": listing.price_else_highest_bid, "has_bid": has_bid})

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "isWatchlist": isWatchlist,
        "form": form,
        "comments": comments,
        "comment_form": CommentForm(),
        "seller": seller
    })
 

class ListingForm(forms.Form):
    title = forms.CharField(label="", widget=forms.TextInput(attrs={"placeholder": "Title", "class": "form-control"}))
    description = forms.CharField(label="", widget=forms.Textarea(attrs={"placeholder": "Enter description", "rows":4, "class": "form-control"}))
    image_url = forms.URLField(label="", required=False, widget=forms.TextInput(attrs={"placeholder": "Image URL", "class": "form-control"}))
    price = forms.DecimalField(label="", decimal_places=2, widget=forms.NumberInput(attrs={"placeholder": "Price", "class": "form-control"}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Select a category", label="Choose a category", required=False, widget=forms.Select(attrs={"class": "form-control"}))


class BiddingForm(forms.Form):
    bid_amount = forms.DecimalField(
        label="", 
        widget=forms.NumberInput(attrs={"placeholder": "Bid", "class": "form-control"}))
     
    listing_price = forms.DecimalField(required=False, widget=forms.HiddenInput())
    has_bid = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean_bid_amount(self):
        bid_amount = self.cleaned_data.get("bid_amount")

        # Using self.cleaned_data makes the values None, used self.data instead
        # Convert self.data to its actual data type
        listing_price = Decimal(self.data.get("listing_price"))
        has_bid = self.data.get("has_bid")
        has_bid = has_bid.lower() == "true"
 
        if has_bid and bid_amount <= listing_price:
            raise forms.ValidationError("Your bid must be higher than the placed bid.")
        
        if not has_bid and bid_amount < listing_price:
            raise forms.ValidationError("Your bid must be higher than the listing price.")
    
        return bid_amount
        
class CommentForm(forms.Form):
    text = forms.CharField(label="", widget=forms.TextInput(attrs={"placeholder": "Write a comment...", "class": "form-control"}))

