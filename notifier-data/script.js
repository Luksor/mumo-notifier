function save(){
    $.post("/submit", function(data) {
        alert("Saved!");
    });
}

function getURLParameter(name){
    var url = window.location.search.substring(1);
    var parameters = url.split("&");
    for(var i = 0; i < parameters.length; i++)
    {
        var paramKV = parameters[i].split("=");
        if(paramKV[0] === name)
        {
            return paramKV[1];
        }
    }
    return null;
}

var collapsed = []

function toogleFeeds(ev) {
    let feeds = $(ev).parent().parent()
    let feedsid = feeds.attr('id')
    if(!collapsed[feedsid]) {
        collapsed[feedsid] = feeds.height()
        feeds.css("height", 64)
        $(ev).css("transform", "rotate(180deg)")
    }else {
        feeds.css("height", collapsed[feedsid])
        delete collapsed[feedsid]
        $(ev).css("transform", "rotate(0deg)")
    }
}

$(document).ready(function(){
    
    var token = getURLParameter("token");
    if(token == null){
        alert("Token is required. Type !notifier in Mumble chat to access this panel.");
        throw new Error();
    }
    
    $(document).ready(function() {
        $.ajax({
            url: '/user',
            type: 'GET',
            dataType: 'json',
            success: function(data) { 
                $("#user").html(data.name);
                $.getJSON('/feeds', function(data) {
                    for (var feedId in data["feeds"]) {
                        var feedInfo = feedId.split("-");
                        var feed = data["feeds"][feedId]
                        if($(`#feeds-${feedInfo[0]}`).length == 0) {
                            $("#main").append(`
                                <div id="feeds-${feedInfo[0]}" class="feeds">
                                    <div class="header">
                                        <input class="feedSubscribe" type="checkbox">
                                        <div class="feedName">${feedInfo[0]}</div>
                                        <div class="dropdown" onclick="toogleFeeds(this)">▲</div>
                                    </div>
                                </div>`)
                        }
                        $(`#feeds-${feedInfo[0]}`).append(`
                            <div id="feed-${feedId}" class="feed">
                                <input class="feedSubscribe" type="checkbox">
                                <div class="feedName">${feedId}</div>
                                <div class="feedLabel" style="background-color: ${feed["color"]}">${feedInfo[1]}</div>
                            </div>`)
                    }
                    for (var feeds of $(".feeds")) {
                        var feeds = $(feeds)
                        feeds.css("height", feeds.height())
                    }
                    $("#main").append(`<button type="button" onclick="save()" class="save-btn">Save</button>`);
                });
            },
            error: function() { 
                alert("Unable to get user info.");
                throw new Error();
            },
            beforeSend: setTokenHeader
        });
    });

    function setTokenHeader(xhr) {
        xhr.setRequestHeader('Token', token);
    }
});
