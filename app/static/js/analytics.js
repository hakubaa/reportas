function loadSchema(request, callback) {
    if (request === undefined) request = {};
    if (request.fschema === undefined || request.company === undefined || 
            request.timerange === undefined) {
        throw "Defective request: fschema, company & timerange are required.";
    }

    var request_url = "http://localhost:5000/api/fschemas/" + 
        request.fschema + "/records?company=" + request.company + "&" +
        "&timerange=" + request.timerange + "&format=T";

    $.getJSON(request_url).done(function(data) {
        callback(data);
    });
}


function wrapWith(wrapper, elements, attributes) {
    if (attributes === undefined) attributes = {};
    if (!$.isArray(elements)) {
        elements = [elements];
    }
    var $wrapper = $("<" + wrapper + "></" + wrapper + ">", attributes);
    for(var i = 0; i < elements.length; i++) {
        $wrapper.append(elements[i]);
    }
    return $wrapper;       
}


function createTable(data, attributes) {
    var $headers = $("<tr></tr>");
    $headers.append("<th>Financial Record</th>");
    data.data.forEach(function(data, index) {
        $headers.append(createHeaderCell(data));
    });

    var rows = new Array(data.schema.length);
    data.schema.forEach(function(item) {
        var $row = $("<tr></tr>");
        $row.attr("data-rtype", item.rtype.name);
        $row.append(createCellWithRType(item.rtype.name));
        rows[item.position] = $row;
    });

    var rdata = sortByTimestamp(data.data);
    rdata.forEach(function(data, index) {
        data.records.forEach(function(item) {
            rows[item.position].append(createCellWithRecord(item.record));
        });
    });

    var $table = wrapWith("table", [
        wrapWith("thead", $headers),
        wrapWith("tbody", rows)
    ], attributes);

    return $table;
}

function sortByTimestamp(data) {
    var rdata = $.extend(true, [], data);
    rdata.sort(function(x, y) {
        return moment(x.timestamp) - moment(y.timestamp);
    });  
    return rdata;
}

function createHeaderCell(data) {
    var timestamp = moment(data.timestamp);
    return $("<th>" + timestamp.format("YYYY-MM") + "</th>");    
}

function createCellWithRType(rtype) {
    return wrapWith("td", $("<span>" + rtype + "</span>"));
}

function createCellWithRecord(record) {
    if (record === null) {
        return $("<td></td>");
    }
    var $cell = $("<td>" + record.value + "</td>");
    $cell.attr("data-id", record.id);
    return $cell;
}