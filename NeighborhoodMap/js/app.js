var map, infowindow;
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
                        initLocation = results;
                        getYelp(getNums(initLocation.formatted_phone_number));
                        
                        //--------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>put yelp stuff here when it works

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


function getYelp(tn) {
//start yelp add in
    function nonce_generate() {
        return (Math.floor(Math.random() * 1e12).toString());
    };

var Consumer_Key = 'XXXXXXXX';
var Consumer_Secret = 'XXXXXXXX';
var Token = 'XXXXXXXX';
var Token_Secret = 'XXXXXXXX';

        var yelp_url = 'https://api.yelp.com/v2/phone_search?phone=' + tn ;

        var parameters = {
                callback: 'cb',
                oauth_consumer_key: Consumer_Key,
                oauth_nonce: nonce_generate(),
                oauth_signature_method: 'HMAC-SHA1',
                oauth_timestamp: Math.floor(Date.now() / 1000),
                oauth_token: Token,
                oauth_version: '1.0',
                phone_search: tn
            };
            //Generate Oauth signature
        encodedSignature = oauthSignature.generate('GET', yelp_url, parameters, Consumer_Secret, Token_Secret);
        parameters.oauth_signature = encodedSignature;
        console.log(encodedSignature)

        var request = {
            url: yelp_url,
            data: parameters,
            cache: true,
            dataType: 'jsonp',
            success: function(results) {
                console.log(results);
            }
        };
    $.ajax(request);
};
//end yelp add in


var Location = function(data, viewModel) {
    var self = this;
    this.name = data.name;
    this.position = data.geometry.location.toString();
    this.phone = data.formatted_phone_number;
    // this.ratingYELP = yelp.rating;
    // this.infoWinContent = yelp.infoWinContent;
    // this.attribution = data.attribution;

    this.clickLocation = function(location) {
        google.maps.event.trigger(this.marker, 'click');
        viewModel.pickLocation(self.name);
    };

    this.createMarker = ko.computed(function() {
        if (viewModel.google()) {
            self.marker = new google.maps.Marker({
                map: map,
                position: data.geometry.location,
                name: data.name,
                animation: google.maps.Animation.DROP,
            });

            infowindow = new google.maps.InfoWindow();

            self.marker.addListener('click', function() {
                infowindow.close();
                infowindow.setContent('<div>' + data.name + '</div>');
                infowindow.open(map, this);
                viewModel.pickLocation(self.name);

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
    this.locationsList = ko.observableArray([]);
    this.google = ko.observable(false);
    this.filter = ko.observable('');
    this.currentLocation = ko.observable(self.locationsList()[0]);

    this.pickLocation = function(newtitle) {
        self.currentLocation(newtitle);
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
        center: {
            lat: 32.6660657,
            lng: -116.95416449999999
        }
    });

    google.maps.event.addListener(map, 'click', function(event) { //added this to recenter map on click.  Need to make it work.
        console.log(event)
        center = event.latLng;
    });

    getLocations(); //fires API call
    viewModel.google(true);
};

var viewModel = new ViewModel();
ko.applyBindings(viewModel);