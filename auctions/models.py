from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class AuctionListing(models.Model):
    FASHION = "FAS"
    TECHNOLOGY = "TEC"
    TOYS = "TOY"
    HOME = "HOM"
    OTHER = "OTH"

    CATEGORIES = [
        (FASHION, "Fashion"),
        (TECHNOLOGY, "Technology"),
        (TOYS, "Toys"),
        (HOME, "Home"),
        (OTHER, "Other")
    ]


    # Primary key id automatically made
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    winner = models.CharField(max_length=150, blank=True, default="")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=512)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2) # Max is $ 99,999,999.99
    buyout = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_time = models.DateTimeField(auto_now_add=True) # Set time to when listing is made
    duration = models.DurationField()
    closed = models.BooleanField(default=False)
    image = models.URLField(blank=True)
    category = models.CharField(max_length=3, choices=CATEGORIES, default=OTHER)
    

    def __str__(self):
        return f"{self.title} being sold by {self.seller}"
    
class Watch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="watchlist")

    def __str__(self):
        return f"{self.user} is watching {self.listing}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=512)
    time = models.DateTimeField(auto_now=True) # Set time to now everytime object is saved

    def __str__(self):
        return f"{self.user} said \"{self.comment}\" about {self.listing}. Posted on {self.time}."

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="bids")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    time = models.DateTimeField(auto_now_add=True) # Set time to when bid is first made

    def __str__(self):
        return f"{self.user} placed a {self.price} bid on {self.listing} on {self.time}"
