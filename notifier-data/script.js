$(document).ready(function(){
    $.getJSON('feeds.json', function(data) {
        for (var feed in data["feeds"]) {
            feedInfo = feed.split("-");
            if($("#" + feedInfo[0]).length == 0) {
                $(".panel-body").append('<div class="list-group" id="' + feedInfo[0] + '"><a class="list-group-item disabled">' + feedInfo[0] + '</a></div>');
            }
            $("#" + feedInfo[0]).append('<a class="list-group-item" id="' + feed + '" style="text-align: left;"><input type="checkbox" style="float: left;">&nbsp;' + feed + '&nbsp;</a>');
            $("[id='" + feed + "']").append('<span class="label label-info" style="float: right; background-color: ' + data["feeds"][feed]["color"] + ';">' + feedInfo[1] + '</span>');
        }
        $(".panel-body").append('<button type="button" onclick="alert(\'Saved!\')" class="btn btn-success">Save</button>');
    });
});
