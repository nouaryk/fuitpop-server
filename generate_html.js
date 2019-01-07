function file_exists(filename) {
	var response = jQuery.ajax({
		url: filename,
		type: 'HEAD',
		async: false
	}).status;	
	return (response != "200") ? false : true;
}

function get_json_data(url) {
    var j = [];
    if (file_exists(url)) {
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            success: function(data) { j = data;},
            error: function(){},
            async: false
        });
    }
    return j;
}

function add_days(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }

function last_race_html(elemId) {
    var api_filename = "data/Calendar_" + new Date().getFullYear() + ".json";
    var data = get_json_data(api_filename);
    var races = data['MRData']['RaceTable']['Races'];
    var json_filename = null;

    for (var i = 0; i < races.length; i++) {
        // Get day after date
        var date = new Date(races[i]['date']);
        var newDate = add_days(date, 1);
        cand_filename = newDate.toISOString().slice(0,10) + ".json";
        
        if (file_exists(cand_filename)) {
            // Last race not found
            json_filename = cand_filename;
        } else if (i == 0) {
            // No races have started
            document.getElementById(elemId).innerHTML = "<div class=\"column is-full\">No data available.</div>";
            return;
        } else {
            // Last race found
            console.log(json_filename);
            drivers_html(elemId, json_filename);
            return;
        }
    }
}

function championship_html(elemId) {
    // Get the JSON filename
    var data = get_json_data('data/Championship_' + new Date().getFullYear()  + '.json');
    var html = "";

    // Error handling
    if (data.length == 0) {
        document.getElementById(elemId).innerHTML = "<div class=\"column is-full\">No data available.</div>";
        return;
    }

    // Create the HTML required for each driver
    count = 0;
    for(var key in data) {
        count++;
        theDriver = data[key];
        html += "<tr><th>" + count + "</th>";
        html += "<td>" + theDriver['First Name'] + " " + theDriver['Last Name'] + "</td>";
        html += "<td>" + theDriver['Points'] + "</td></tr>";
    }
    document.getElementById(elemId).innerHTML = html;
}

function daily_drivers_html(elemId) {
    var json_filename = "data/" + new Date().toISOString().slice(0,10) + ".json";
    drivers_html(elemId, json_filename);
}

function drivers_html(elemId, json_filename) {
    // Get the JSON filename using date
    var data = get_json_data(json_filename);
    var data;
    var html = "";
    var showLength = 8;

    // Error handling
    if (data.length == 0) {
        document.getElementById(elemId).innerHTML = "<div class=\"column is-full\">No data available.</div>";
        return;
    }

    // Find total number of tallies to do a percentage
    var sum = 0;
    for(var i = 0; i < showLength; i++) {
        var obj = data[i];
        sum += obj['Tally'];
    }

    // Create the HTML required for each driver
    for(var i = 0; i < showLength; i++) {
        var obj = data[i];
        var imageName = obj['First Name'] + "_" + obj['Last Name'];
        var driverName = obj['First Name'] + " " + obj['Last Name'];
        var percentage = Math.round(obj['Tally']/sum*100);

        // CSS modifier logic for the podium places
        var classModifier = "";
        var imageSizeModifier = "is-one-fourth";
        var imageClass = "is-128x128";
        if (i == 0) {
            classModifier = "podium first";
            imageSizeModifier = "is-one-third";
            imageClass = "is-square";
        }
        else if (i == 1) {
            classModifier = "podium second";
            imageSizeModifier = "is-one-third";
            imageClass = "is-square";
        }
        else if (i == 2) {
            classModifier = "podium third";
            imageSizeModifier = "is-one-third";
            imageClass = "is-square";
        }
        
        // HTML
        html += "<div class=\"column is-horizontal-center driver-wrapper " + imageSizeModifier + "\">";
        html += "<figure class=\"image " + imageClass + "\">";
        html += "<img class=\"driver-image is-rounded " + classModifier + "\" src=\"images/" + imageName + ".jpg\">";
        html += "</figure>";
        html += "<p class=\"heading\">" +  driverName + "</p>";
        html += "<p class=\"title\">" + percentage +  "%</p></div>";
    }
    document.getElementById(elemId).innerHTML = html;
}