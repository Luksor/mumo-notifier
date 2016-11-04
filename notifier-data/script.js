function save(){
    $.post("/submit", function(data) {
        alert("Saved!");
    });
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
    $.getJSON('feeds.json', function(data) {
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
});
