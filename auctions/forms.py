from .models import User, AuctionListing, Bid, Comment, Watch

from django import forms

FASHION = "FAS"
TECHNOLOGY = "TEC"
TOYS = "TOY"
HOME = "HOM"
OTHER = "OTH"

CATEGORY_CHOICES= [
    (FASHION, "Fashion"),
    (TECHNOLOGY, "Technology"),
    (TOYS, "Toys"),
    (HOME, "Home"),
    (OTHER, "Other")
]


DURATION_CHOICES = [
    (7, "7 days"),
    (30, "30 days"),
    (90, "3 months"),
    (180, "6 Months"),
    (365, "1 Year")
]

class NewListingForm(forms.Form):
    title = forms.CharField(max_length=64)
    image = forms.URLField(required=False)
    description = forms.CharField(max_length=512)
    starting_bid = forms.DecimalField(max_digits=10, decimal_places=2) # Max is $ 99,999,999.99
    buyout = forms.DecimalField(max_digits=10, decimal_places=2)
    category = forms.ChoiceField(widget=forms.Select, choices=CATEGORY_CHOICES)
    time_limit = forms.ChoiceField(widget=forms.Select, choices=DURATION_CHOICES)
    
class NewBidForm(forms.Form):
    price = forms.DecimalField(max_digits=10, decimal_places=2, min_value= 0,max_value=99999999.99)

class NewCommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, max_length=512, label="")