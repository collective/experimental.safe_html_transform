/* Session cookie refresh support */
/*jslint browser: true, devel: true */
/*global jQuery: false*/

(function($) {
    
var last_activity = new Date();

function sessionActivity() {
    last_activity = new Date();
}

function startSessionRefresh(index) {
    var url_last_refresh = new Date();
    var url = this.href;
    var match = url.match(new RegExp("[\\?|&]minutes=([^&#]*)"));
    var minutes = match ? parseFloat(match[1]) : null;
    minutes = minutes  ? minutes : 5.0;

    if (typeof(console) != "undefined" && console.info) {
        console.info('Setting up ' + url +
            ' to refresh every ' + minutes + ' minutes.');
    }

    function sessionRefresh() {
        if (last_activity > url_last_refresh) {
            url_last_refresh = new Date();
            new Image().src = url;
            if (typeof(console) != "undefined" && console.info) {
                console.info( '[' + url_last_refresh.toTimeString()  +
                    '] Refreshing session: ' + url +
                    ' (Last Activity: ' + last_activity.toTimeString()  + ')');
            }
        } else {
            if (typeof(console) != "undefined" && console.info) {
                console.info(
                    '[' + new Date().toTimeString() +
                    '] Skipped refresh: ' + url +
                    ' (Last Activity: ' + last_activity.toTimeString()  + ')');
                }
        }
    }
    setInterval(sessionRefresh, minutes * 60 * 1000);
}

$(document).ready(function () {
    $('body').bind('mouseover click keydown', sessionActivity);
    $("head link[rel='stylesheet'][href*='?session_refresh=true']").each(startSessionRefresh);
});

})(jQuery);
