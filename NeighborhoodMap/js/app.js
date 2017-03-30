var map, infowindow;
var initLocations = [];
var center = {lat: 32.6660657,lng: -116.95416449999999};


//start Model
function getLocations() {
  var request = {
    location: center,
    radius: 1000,
    types: ['store']
  };

  service = new google.maps.places.PlacesService(map);
  service.nearbySearch(request, callback);
// }

function callback(results, status) {
  if (status === google.maps.places.PlacesServiceStatus.OK) {
    for (var i = 0; i < results.length; i++) {
      initLocations[i] = results[i];
    };
  }else{
    window.alert('Error:  ' + status)};
};

};

// var initLocations = [ //initialize locations
//     {
//         title: 'Norms House',
//         latlng: {
//             lat: 32.6660657,
//             lng: -116.95416449999999
//         },
//         attribution: 'Norm lives here and provided all data'
//     }, {
//         title: 'Pizzos Pizza',
//         latlng: {
//             lat: 32.6615697,
//             lng: -116.97054700000001
//         },
//         attribution: 'Pizzo lives here and provided all data'
//     }
// ];


var Location = function(data, viewModel) {
    var self = this;
    this.name = data.name;
    console.log(data.name)
    this.position = data.geometry.location.toString();
    // this.attribution = data.attribution;

    this.clickLocation = function(location) {
        google.maps.event.trigger( this.marker, 'click' );
        viewModel.pickLocation(self.name);
    };


    this.createMarker = ko.computed(function() {
        if (viewModel.google()) {
            self.marker = new google.maps.Marker({
                map: map,
                position: data.geometry.location,
                title: data.name,
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

            viewModel.markers.push(self.marker);
        // }
        // else{
        // 	console.log(viewModel.google())
        // 	window.alert('Loading !')
        };
    });
};    //end model


//ViewModel	
var ViewModel = function() {
    console.log(initLocations)  //  I can see this in console, but it doesn't get to the Locations model
    var self = this;
    this.locationsList = ko.observableArray([]);
    this.markers = ko.observableArray([]);
    this.google = ko.observable(false);

    initLocations.forEach(function(locationItem) {  //  This isn't working.  Can't read property location of undefined.
        console.log(locationItem)
        self.locationsList.push(new Location(locationItem, self));
    });

    this.currentLocation = ko.observable( self.locationsList()[0]);

    this.pickLocation = function(newtitle) {
            self.currentLocation(newtitle);
    };

}; //end viewModel


function errorMessage() {
    alert('Google Maps failed to load!');
};


//load map
var callBack = function() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 11,
        center: {
            lat: 32.6660657,
            lng: -116.95416449999999
        }

    });

    getLocations();  //fires API call

    viewModel.google(true);
};

var viewModel = new ViewModel();

ko.applyBindings(viewModel);

