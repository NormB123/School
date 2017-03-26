var map;
var center;
// var viewModel;
// var init = function () {
var markers = [];


//start Model
var initLocations = [ //initialize locations
    {
        title: 'Norms House',
        latlng: {
            lat: 32.6660657,
            lng: -116.95416449999999
        },
        attribution: 'Norm lives here and provided all data'
    }, {
        title: 'Pizzos Pizza',
        latlng: {
            lat: 32.6615697,
            lng: -116.97054700000001
        },
        attribution: 'Pizzo lives here and provided all data'
    }
];


var Location = function(data) {
    var self = this;
    this.title = data.title;
    this.latlng = data.latlng;
    this.attribution = data.attribution;
    this.marker;
    this.infowindow;
    this.clickLocation;

    this.clickLocation = function(location) {
        // self.clickMarker;
        // this.marker.click;
        window.alert(location.title);
    };


    // setTimeout(function() {
    // // Create a marker per location, and put into markers array.
    this.createMarker = ko.computed(function() {
    	console.log(viewModel)
        if (viewModel.google()) {
            self.marker = new google.maps.Marker({
                map: map,
                position: data.latlng,
                title: data.title,
                animation: google.maps.Animation.DROP,
            });

            self.infowindow = new google.maps.InfoWindow();

            marker.addListener('click', function() {
                infowindow.setContent('<div>' + data.title + '</div>');
                self.clickLocation(this);
                infowindow.open(map, this);
            });

            // this.clickLocation = function(location) {
            // 	// self.clickMarker;
            // 	// $("locationData").click(function() {
            // 	// self.marker.click();
            // 	window.alert(location.title);
            // // });
            // };

            markers.push(marker);
        }else{
        	window.alert('Error loading!')
        };
    });

    // }, 400);

};    //end model


//ViewModel	
var ViewModel = function() {
    var self = this;
    this.locationsList = ko.observableArray([]);
    this.google = ko.observable(false);

    initLocations.forEach(function(locationItem) {
        self.locationsList.push(new Location(locationItem));
    });

}; //end viewModel


function errorMessage() {
    alert('Google Maps failed to load!');
};


//load map
var callBack = function() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,
        center: {
            lat: 32.6660657,
            lng: -116.95416449999999
        }
    });

    viewModel.google(true);
};

var viewModel = new ViewModel();

ko.applyBindings(viewModel);

