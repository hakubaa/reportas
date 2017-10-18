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
    $headers.append("<th></th>");
    $headers.append("<th>Financial Record</th>");
    data.data.forEach(function(data, index) {
        $headers.append(createHeaderCell(data));
    });

    var rows = new Array(data.schema.length);
    data.schema.forEach(function(item) {
        var $row = $("<tr></tr>");
        $row.attr("data-rtype", item.rtype.name);
        $row.attr("data-rtype-id", item.rtype.id);
        $row.append(wrapWith("td", createAddToChartBtn()));
        $row.append(createCellWithRType(item.rtype));
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

function createAddToChartBtn() {
    var chartBtn = wrapWith("button",
        $("<span></span>", {"class": "glyphicon glyphicon-stats"}),
        {"class": "btn btn-xs btn-link btn-add-to-chart"}
    ); 
    return chartBtn;
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
    // return wrapWith("td", 
    //     $("<a class='rtype-btn' href='javascript:void(0);''>" + rtype.name + "</a>")
    // );
    return wrapWith("td", 
        $("<a href='#chart-modal' data-toggle='modal' data-target='#chart-modal'>" + rtype.name + "</a>")
    );
}

function createCellWithRecord(record) {
    var $cell = $("<td></td>");
    if (record !== null) {
        $cell.html(record.value);
        $cell.attr("data-id", record.id);
        $cell.attr("data-value", record.value);
    }
    $cell.addClass("record-value");
    return $cell;
}

jQuery.fn.fillSelect2WithAjax = function(url, attributes) {
    var self = this;
    $.getJSON(url).done(function(data) {
        for(var i = 0; i < self.length; i++) {
            $(self[i]).fillSelect2WithData(data.results, attributes);
        }
    });
}

jQuery.fn.fillSelect2WithData = function(data, attributes) {
    var attrs = {id: "id", label: "text"};
    $.extend(attrs, attributes);

    if ($(this).hasClass("select2-hidden-accessible")) {
        $(this).select2("destroy");
    }

    var select = this;
    $.each(data, function() {
        $(select).append(
            $("<option/>").val(this[attrs.id]).text(this[attrs.label])
        );
    });


    this.applySelect2(attrs);
}

jQuery.fn.applySelect2 = function(attributes) {
    var attrs = {
        dropdownAutoWidth: true,
        placeholder: {
            id: "none",
            value: "-1",
            text: "Select an option",
        },
    };
    $.extend(attrs, attributes);

    for(var i = 0; i < this.length; i++) {
        $(this[i]).select2(attrs);
    }
}    

function distinct(array, key) {
    if (key === undefined) key = function(item) { return item; };
    var flags = [];
    var output = [];
    for(var i = 0; i < array.length; i++) {
        if (flags[key(array[i])]) continue;
        flags[key(array[i])] = true;
        output.push(array[i]);
    }
    return output;
}

function isSelectValid(selector) {
    var $selectElement = $(selector);
    return $selectElement.val() !== null;
}

function getSelectVal(selector) {
    var $selectElement = $(selector);
    return $selectElement.find("option:selected").val();
}

function getSelectText(selector) {
    var $selectElement = $(selector);
    return $selectElement.find("otpion:selected").text();
}

function loadData(request, callback) {
    var request_url = "http://localhost:5000/api/companies/" + 
        request.company + "/records?filter=rtype_id=" + 
        request.rtype + ";timerange=" + request.timerange;

    $.getJSON(request_url).done(function(data) {
        data.results.forEach(function(item) {
            item.timestamp = moment(item.timestamp);
        });
        callback(data.results);
    });
}

function formatTimestamp(timestamp, format) {
    if (format === undefined) format = "YYYY-MM";
    return timestamp.format(format);
}

jQuery.fn.formatRecords = function(callback) {
    for(var i = 0; i < this.length; i++) {
        formatNumbers($(this[i]), callback);
    }
    return this; 
};

function formatNumbers($table, callback) {
    var records = $table.find(".record-value");
    records.each(function() {
        if (callback !== undefined) {
            $(this).html(callback($(this).attr("data-value")));
        }
    });
}