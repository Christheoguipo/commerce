from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=100, blank=False) 
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.name}"
 

class Listing(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=False)
    url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @property
    def price_else_highest_bid(self):
        highest_bid = Bid.objects.filter(listing=self).order_by("-amount").first()

        if highest_bid:
            return highest_bid.amount
        else: 
            return self.price
    
    @property
    def highest_bidder(self):
        highest_bid = Bid.objects.filter(listing=self).order_by("-amount").first()

        if highest_bid:
            return highest_bid.user


    def __str__(self):
        return f"{self.id}: {self.title} {self.description} {self.url} {self.price} {self.category} {self.active} {self.user}"


class Bid(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=7, blank=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    date = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.id}: {self.listing} {self.amount} {self.user}" 


class Comment(models.Model):
    text = models.TextField()
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.text} {self.listing} {self.user}" 
    

class Watchlist(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.listing} {self.user}" 