(function(angular, undefined) {
'use strict';

var module = angular.module('django.shop.checkout', []);

module.controller('checkoutPurchaseCtrl', ['$http', '$q', '$scope', function($http, $q, $scope) {
	var self = this;
    console.log('checkoutPurchaseCtrl');
    $scope.lock = false;

	$scope.is_disabled = function(is_empty) {
        if (is_empty == 'True' || $scope.lock == true)
            return true;
        return false;
    }

	$scope.purchaseNow = function(endpoint) {
        $scope.lock = true;
		var deferred = $q.defer();
		$http.post(endpoint).then(function(response) {
            eval(response.data.expression);
			deferred.resolve(response);
		});
		return deferred.promise;
	};
}]);

})(window.angular);
