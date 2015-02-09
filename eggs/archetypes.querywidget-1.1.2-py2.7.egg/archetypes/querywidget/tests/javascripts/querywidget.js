// Create executed property
$.querywidget.executed = [];

// Create dummy stub function
$.querywidget.dummy = function () {
    $.querywidget.executed.push("dummy");
};

// Create ajax stub function
$.ajax = function (options) {
    options.success("{test: 1}");
};

module("querywidget", {
    setup: function () {
        // We'll create a div element for the dialog
        $(document.body)
            .append(
                $(document.createElement("div"))
                    .attr("id", "content")
            );

        // Empty executed
        $.querywidget.executed = [];
    },
    teardown: function () {
        $("#content").remove();
    }
});

test("Initialisation", function () {
    expect(1);

    ok($.querywidget, "$.querywidget");
});
