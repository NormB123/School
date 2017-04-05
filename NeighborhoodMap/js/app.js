var map;
var infowindow; // = [];
var markers = [];
var center = {
    lat: 32.6660657,
    lng: -116.95416449999999
};


//start Model
function getLocations() { //Get nearby places from google maps
    var initDetails = [];

    var request = {
        location: center,
        radius: 3000,
        types: ['bar']
    };

    service = new google.maps.places.PlacesService(map);
    service.nearbySearch(request, callbackPlaces);

    function callbackPlaces(results, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            for (var i = 0; i < results.length; i++) {
                initDetails[i] = results[i].place_id;

                service = new google.maps.places.PlacesService(map); //get details from google maps
                service.getDetails({
                    placeId: initDetails[i]
                }, callbackDetails);

                function callbackDetails(results, status) { //handle returned details
                    if (status === google.maps.places.PlacesServiceStatus.OK) {

                        var tn = results.formatted_phone_number.replace(/\D/g,'');

                        //start yelp add in
                        function nonce_generate() {
                            return (Math.floor(Math.random() * 1e12).toString());
                        };

                        var infoWinContent = '';
                        var Consumer_Key = 'k8say9OyiDgX8Qs5aqqf0Q';
                        var Consumer_Secret = 'Z7sjQjYnUkO6AlK5FSxqFG7JijM';
                        var Token = 'Nsd5ytSzAGZM9M6tfaCawOQSsxNIk9Td';
                        var Token_Secret = 'o5we2MF68uzUSbOuI58VQnTIHfM';

                        var yelp_url = 'https://api.yelp.com/v2/phone_search?'

                        var parameters = {
                            callback: 'cb',
                            oauth_consumer_key: Consumer_Key,
                            oauth_nonce: nonce_generate(),
                            oauth_signature_method: 'HMAC-SHA1',
                            oauth_timestamp: Math.floor(Date.now() / 1000),
                            oauth_token: Token,
                            oauth_version: '1.0',
                            phone: tn
                        };
                        //Generate Oauth signature
                        encodedSignature = oauthSignature.generate('GET', yelp_url, parameters, Consumer_Secret, Token_Secret);
                        parameters.oauth_signature = encodedSignature;

                        var request = {
                            url: yelp_url,
                            data: parameters,
                            cache: true,
                            dataType: 'jsonp',
                            success: function(data) {
                                var name = data.businesses[0].name,
                                    phone = data.businesses[0].display_phone,
                                    ratingImg = data.businesses[0].rating_img_url,
                                    rating = data.businesses[0].rating.toString(),
                                    link = data.businesses[0].url,
                                    image = data.businesses[0].image_url;
                                    address = data.businesses[0].location.display_address;

                                var infowin = [{name: name, phone: phone, ratingImg: ratingImg, 
                                    rating: rating, link: link, image: image, address: address}];

                                viewModel.markerInfoWin.push(infowin[0]);
                            },
                            fail: function(data) {
                                window.alert('Yelp content failed to load.  Reload Page.  If condition persists, contact site administrator.')
                            }
                        };
                        $.ajax(request);
                        //end yelp add in

                        initLocation = results;

                        viewModel.locationsList.push(new Location(initLocation, viewModel));
                    } else {
                        window.alert('Details Error:  ' + status)
                    };
                };
            };
        } else {
            window.alert('Search Error:  ' + status)
        };
    };
}; // end getLocations

var Location = function(data, viewModel) {
    var self = this;
    this.name = data.name;
    this.position = data.geometry.location.toString();
    this.phone = data.formatted_phone_number;

    this.clickLocation = function(location) {  //---------------------->>> fires pickLocation which sets currentLocation
        google.maps.event.trigger(this.marker, 'click');
        viewModel.pickLocation(self);  //.phone)
    };

    this.createMarker = ko.dependentObservable(function() {
        if (viewModel.google()) {
            self.marker = new google.maps.Marker({
                map: map,
                position: data.geometry.location,
                name: data.name,
                animation: google.maps.Animation.DROP,
            });

            infowindow = new google.maps.InfoWindow();

            self.marker.addListener('click', function() {
                viewModel.pickLocation(self);
                infowindow.close();
                infowindow.setContent('<div><p><h1>' + infowindowdata.name + '</h1></p></div><p><strong>Address: </strong>' + infowindowdata.address + '</p>' + '<p><strong>Phone: </strong>' + infowindowdata.phone + 
                '</p>' + '<p><strong>Yelp Stars: </strong>' + '<img src="' + infowindowdata.ratingImg + '"></p>' + 
                '<p><strong>Rating : </strong>' + infowindowdata.rating + '</p>' + '<p><a href="' + infowindowdata.link + '">Learn more: </a></p>' + '</div>');//(viewModel.currentInfoWin);  //('<div>' + data.name + '</div>');
                infowindow.open(map, this);

                self.marker.setAnimation(google.maps.Animation.BOUNCE);
                setTimeout(function() {
                    self.marker.setAnimation(null);
                }, 2200);
            });
        };
        markers.push(self.marker);
    });
}; //end Location model


//ViewModel 
var ViewModel = function() {
    var self = this;
    this.locationsList = ko.observableArray([]); //change this to reset list after search
    this.markerInfoWin = ko.observableArray([]); 
    this.google = ko.observable(false);
    this.filter = ko.observable('');
    this.currentLocation = ko.observable(self.locationsList()[0]);
    this.infowindowdata;

    this.pickLocation = function(newlocation) {
        self.currentLocation(newlocation);  //--------------->>>  sets currentLocation when clicked on DOM
        newinfo = getNums(newlocation.phone);
        for (var i = 0; i < self.markerInfoWin().length; i++) {
            var oldinfo = getNums(self.markerInfoWin()[i].phone).substring(1);
            if (newinfo === oldinfo) {
                infowindowdata = self.markerInfoWin()[i];
            }
        };
    };

    //    filter the items using the filter text
    this.filteredItems = ko.dependentObservable(function() {
        var filter = self.filter().toLowerCase();
        if (!filter) {
            restoreAllMarkers();
            return self.locationsList();
        } else {
            infowindow.close();
            return ko.utils.arrayFilter(self.locationsList(), function(locationsList) {
                locationsList.marker.setVisible(false);
                if (locationsList.name.toLowerCase().indexOf(filter) !== -1) {
                    locationsList.marker.setVisible(true);
                    return locationsList;
                }
            });
        }
    }, this);
}; //end viewModel


function restoreAllMarkers(map) {
    for (var i = 0; i < markers.length; i++) {
        infowindow.close();
        markers[i].setVisible(true);
    }
};

function getNums(str) {
    return str.replace(/\D/g,'');
}

function errorMessage() {
    alert('Google Maps failed to load!');
};


//load map
var callBack = function() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 14,
        center: center
    });


google.maps.event.addListener(map, 'click', function(event) { 
        center = event.latLng;
        infowindow.close();
        viewModel.locationsList.removeAll();
        $(".clearMe").empty();
        callBack();
    });

    getLocations(); //fires API call
    viewModel.google(true);
};

var viewModel = new ViewModel();
ko.applyBindings(viewModel);