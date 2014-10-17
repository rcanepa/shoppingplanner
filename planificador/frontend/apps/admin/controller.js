function AdminCtrl () {
    var self = this;
    self.dummy = "Hola!";
}

angular.module('adminApp')
    .controller('AdminCtrl', AdminCtrl);