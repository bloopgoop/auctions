from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, AuctionListing, Bid, Comment, Watch
from .forms import NewListingForm, NewBidForm, NewCommentForm

import datetime


def index(request):
    listings = AuctionListing.objects.filter(closed=False)
    return render(request, "auctions/index.html", {"listings": listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
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
def newlisting(request):
    if request.method == "POST":

        # Create new bound form
        form = NewListingForm(request.POST)
        if form.is_valid():

            # Process data
            seller = User.objects.get(username=request.user)
            title = form.cleaned_data["title"]
            image = form.cleaned_data["image"]
            description = form.cleaned_data["description"]
            starting_bid = form.cleaned_data["starting_bid"]
            buyout = form.cleaned_data["buyout"]
            category = form.cleaned_data["category"]
            time_limit = int(form.cleaned_data["time_limit"])
            duration = datetime.timedelta(time_limit)
            
            # Attempt to store in db
            try:
                listing = AuctionListing(
                    seller=seller,
                    title=title,
                    description=description,
                    starting_bid=starting_bid,
                    buyout=buyout,
                    duration=duration,
                    image=image,
                    category=category,
                )
                listing.save()
                id = listing.id
                return HttpResponseRedirect(reverse("listing", args=[id]))

            except Exception as e:
                print(f"Error saving listing: {e}")


    else:
        form = NewListingForm()
        return render(request, "auctions/newlisting.html", {"form": form})

    return render(request, "auctions/newlisting.html", {"form": form})


def get_listing(request, listing):
    """
    auctions/listing.html takes in

    listing: an AuctionListing object
    watching: a boolean representing if the current user has the listing on their watchlist
    bid_form: a NewBidForm object
    comment_form: a NewCommentForm object
    comments: a list of Comment objects
    message: a message to be displayed to the user
    """

    listing = AuctionListing.objects.get(id=listing)
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user)
    watching = Watch.objects.filter(user=user, listing=listing).exists()
    comments = listing.comments.all()

    bid_form = NewBidForm()
    comment_form = NewCommentForm()
    message = "POST form not processed" # default message
    
    # Check if listing is already closed
    if listing.closed:
        return render(request, "auctions/listing.html", {
                "listing": listing,
                "comments": comments,
                "message": "This listing is closed"
            })
    
    # Check if it is time to close it
    else:
        close_time = listing.start_time + listing.duration
        current_datetime = datetime.datetime.now()
        current_datetime = current_datetime.astimezone(None)
        if current_datetime >= close_time:
            close_listing(listing)
            return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "comments": comments,
                    "message": "This listing is closed"
                })




    # Listing is not closed yet, can watchlist, bid, cancel, comment
    if request.method == "POST":

        # Unwatchlist the listing
        if "unwatchlist" in request.POST:
            try:
                Watch.objects.get(user=user, listing=listing).delete()
                watching = False
                message = "This item is no longer in your watchlist"

            except Exception as e:
                message = f"Error removing listing from watchlist: {e}"


        # Watchlist the listing
        elif "watchlist" in request.POST:
            if watching:
                return HttpResponseRedirect("This item is already in your watchlist")
            try:
                obj = Watch(user=user, listing=listing)
                obj.save()
                watching = True,
                message = "This item is now in your watchlist"

            except Exception as e:
                message = f"Error putting listing into watchlist: {e}"

        # Place bid
        elif "bid" in request.POST:
            bid_form = NewBidForm(request.POST)
            if bid_form.is_valid():

                # Sever side validation
                price = bid_form.cleaned_data["price"]
                if price <= listing.current_price or price < listing.starting_bid or price > listing.buyout:
                    return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "watching": watching,
                    "bid_form": bid_form,
                    "comment_form": comment_form,
                    "comments": comments,
                    "message": "Invalid price"
                })

                try:
                    # Store bid in Bid db
                    bid = Bid(
                        user=user,
                        listing=listing,
                        price=price
                    )
                    bid.save()
                    
                    # Update listing
                    listing.current_price = price
                    listing.save()

                    # If bid is a buyout
                    if price == listing.buyout:
                        close_listing(listing)
                        return render(request, "auctions/listing.html", {
                            "listing": listing,
                            "comments": comments,
                            "message": "This listing is closed"
                        })
                    
                    bid_form = NewBidForm()
                    message = "Bid success"
                
                except Exception as e:
                    message = f"Error placing bid {e}"

                
        # Cancel auction
        elif "end" in request.POST:
            close_listing(listing)
            return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "comments": comments,
                    "message": "This listing is closed"
                })
        
        # Comment
        elif "comment" in request.POST:
            comment_form = NewCommentForm(request.POST)
            if comment_form.is_valid():

                comment = comment_form.cleaned_data["comment"]
                try:
                    # Store bid in Bid db
                    obj = Comment(
                        user=user,
                        listing=listing,
                        comment=comment
                    )
                    obj.save()
                    comment_form = NewCommentForm()
                    message = "Comment posted"

                except Exception as e:
                    message = f"Error commenting {e}"

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "watching": watching,
            "bid_form": bid_form,
            "comment_form": comment_form,
            "comments": comments,
            "message": message
            })

    else:
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "watching": watching,
            "bid_form": bid_form,
            "comment_form": comment_form,
            "comments": comments
        })


@login_required
def watchlist(request):
    user = User.objects.get(username=request.user)
    tabs = Watch.objects.filter(user=user)
    listings = []
    for tab in tabs:
        listings.append(tab.listing)
    return render(request, "auctions/index.html", {
        "watchlist": True,
        "listings": listings
    })


def categories(request):
    categories = [category[1] for category in AuctionListing.CATEGORIES]
    return render(request, "auctions/categories.html", {"categories": categories})


def category(request, category):
    for tuple in AuctionListing.CATEGORIES:
        if tuple[1] == category:
            acronym = tuple[0]
            break

    listings = AuctionListing.objects.filter(category=acronym, closed=False)
    return render(request, "auctions/index.html", {
        "category": category,
        "listings": listings
    })


def close_listing(listing):
    try:
        bid = Bid.objects.get(listing=listing, price=listing.current_price)
    except Exception as e:
        print(f"Error closing listing: {e}")
        bid = None

    if bid:
        listing.winner = bid.user.username
    listing.closed = True
    listing.save()