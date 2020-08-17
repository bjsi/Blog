$(function () {
    var timer = null;
    var xhr = null;
    $('a.article').hover(
        function(event) {
            // mouse in event handler
            var elem = $(event.currentTarget);
            timer = setTimeout(function() {
                timer = null;
                xhr = $.ajax(
                    '/article/' + elem.first().attr("slug") + '/popup').done(
                        function(data) {
                            xhr = null;
                            elem.popover({
                                trigger: 'manual',
                                html: true,
                                animation: false,
                                container: elem,
                                content: data
                            }).popover('show');
                        }
                    );
            }, 500);
        },
        function(event) {
            // mouse out event handler
            var elem = $(event.currentTarget);
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            else if (xhr) {
                xhr.abort();
                xhr = null;
            }
            else {
                elem.popover('dispose');
            }
        }
    );
});
