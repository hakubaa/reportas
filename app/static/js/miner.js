var FIXED_COLUMNS = 4;
var UNITS_OF_MEASURE_COLUMN = 3;
var RECORD_TYPE_COLUMN = 2;

//------------------------------------------------------------------------------
// XMLHttpRequests Functions
//------------------------------------------------------------------------------

/**
 * Send XMLHttpRequest for identification of items.
 */
function identifyItems(options) {
    if (options === undefined) options = {};
    if (options.spec === undefined) options.spec = "";
    if (options.text === undefined) {
        throw "Undefined text.";
    }

    $.post(
        "/reports/parser", 
        { text: options.text, spec: options.spec }
    )
        .done(function(response) {
            if (options.callback !== undefined) {
                options.callback(response);
            }
        })
        .fail(function(xhr, textStatus, error){
              console.log(xhr.statusText);
              console.log(textStatus);
              console.log(error);
              alert("Error: " + error);
        });
}

/**
 * Send XMLHttpRequest for list of records types.
 */
function getRecordTypes(options) {
    $.getJSON("/api/rtypes", { fields: "name" }, function(data) {
        var rtypes = data.results.map(function(element) { 
            return element.name;
        });
        if (options.callback !== undefined) {
            options.callback(rtypes);            
        }
    })
        .fail(function(xhr, textStatus, error){
              console.log(xhr.statusText);
              console.log(textStatus);
              console.log(error);
              alert("Error: " + error);
        });
}

//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// jQuery extension
//------------------------------------------------------------------------------
    
jQuery.fn.makeDraggable = function() {
    for(var i = 0; i < this.length; i++) {
        $(this[i]).draggable({
            helper: "clone",
            start: function(even, ui) {
                $(ui.helper).addClass("info");
                $(this).addClass("info");
            },
            stop: function(event, ui) {
                $(this).removeClass("info");
            }
        });
    }
    return this; 
};

jQuery.fn.makeDroppable = function() {
    for(var i = 0; i < this.length; i++) {
        $(this[i]).droppable({
            drop: function(event, ui) {
                if (hasCommonTableAncestor(ui.draggable, this)) {
                    if ($(ui.helper).offset().top > $(this).offset().top) {
                        $(ui.draggable).insertAfter(this);
                    } else {
                        $(ui.draggable).insertBefore(this);
                    }
                    $(this).removeClass("success");
                    $(ui.helper).remove();
                }
            },
            over: function(event, ui) {
                if (hasCommonTableAncestor(ui.draggable, this)) {
                    $(this).addClass("success");
                }
            },
            out: function(event, ui) {
                if (hasCommonTableAncestor(ui.draggable, this)) {
                    $(this).removeClass("success");
                }
            }
        });
    }
    return this;
};

function hasCommonTableAncestor(item1, item2) {
    return ($(item1).closest("table").attr("id") === $(item2).closest("table").attr("id"));
}

jQuery.fn.applySelect2 = function(attributes) {
    var attrs = {
        dropdownAutoWidth: true,
            placeholder: {
                id: "-1",
                text: "Select an option",
            }
    };
    for(var property in attributes) {
        attrs[property] = attributes[property];
    }
    var data = attrs.data;
    var text = attrs.text;
    if (data !== undefined) {
        attrs.data = data;
        if (text !== undefined) {
            data = $.map(rtypes, function (obj) {
                obj.text = obj.text || obj[text]; 
                return obj;
            });
            attrs.data = data;
        }
    }
    for(var i = 0; i < this.length; i++) {
        $(this[i]).select2(attrs);
        if (data !== undefined) {
            var initVal = $(this[i]).data("init-val");
            if (initVal) {
                $(this[i]).val(initVal).trigger("change");
                continue;
            }
            var initText = $(this[i]).data("init-text");
            if (initText) {
                var items = $.grep(data, function(obj) { 
                    return (obj.text == initText); 
                });
                if (items.length > 0) {
                    $(this[i]).val(String(items[0].id)).trigger("change");
                }
            }
        }
    }
}

jQuery.fn.bindUnitsOfMeasure = function() {
    var data = [
        {id: 1, text: "PLN"},
        {id: 1000, text: "k'PLN"},
        {id: 1000000, text: "m'PLN"}
    ];
    $(this).applySelect2({
        data: data,
        minimumResultsForSearch: Infinity,
        placeholder: "Select units"
    });
}

$.fn.singleDatePicker = function(attributes) {
    $(this).on("apply.daterangepicker", function(e, picker) {
        picker.element.val(picker.startDate.format(picker.locale.format));
    });
    var defaultAttributes = {
        singleDatePicker: true,
        showDropdowns: true,
        locale: {
            format: "YYYY-MM-DD"
        },
        autoUpdateInput: false
    };
    for(var property in attributes) {
        defaultAttributes[property] = attributes[property];
    }
    return $(this).daterangepicker(defaultAttributes);
};

$.fn.bindDatePicker = function(attributes) {
    if (attributes === undefined) attributes = {};

    var defaultAttributes = {
        autoclose: true,
        format: "yyyy-mm",
          minViewMode: "months",
          orientation: "top",
          startView: "months"
    };
    for(var property in attributes) {
        defaultAttributes[property] = attributes[property];
    }

    for(var i = 0; i < this.length; i++) {
        $(this[i]).datepicker(defaultAttributes);
    }
};

//------------------------------------------------------------------------------
// Functions for tables with financial records
//------------------------------------------------------------------------------

function activateFocusOnInputs(selector) {
    $(document).on("focusin", selector + " td input", function() {
        $(this).closest("tr").addClass("info"); 
    });
    
    $(document).on("focusout", selector + " td input", function() {
        $(this).closest("tr").removeClass("info"); 
    });
}

function addRowToTable(table, row) {
    if (table === undefined) throw "Undefined table.";
    table.find("tbody").append(row);
    toggleTable(table);
}

function toggleTable(table) {
    var numberOfRows = table.find("tbody tr:visible").not(".empty-row").length;
    if (numberOfRows === 0) { // show empty row
        table.find(".empty-row").show();
        table.find("thead").hide();
    } else {
        var $firstRow = table.find("tbody tr:visible:first");
        if ($firstRow.hasClass("empty-row") && numberOfRows > 0) {
            $firstRow.hide();
            table.find("thead").show();
        } 
    }
}

function addEmptyRow(selector, rtypes) {
    if (selector === undefined) throw "Undefined selector.";
    var numberOfColumns = getNumberOfColumns(selector);
    var $newRow = createNewRecordRow(numberOfColumns);
    $newRow.find(".rtype-selection").applySelect2({
        data: rtypes, text: "name"
    });
    $newRow.find(".units-selection").bindUnitsOfMeasure();
    addRowToTable($(""+selector), $newRow);
}

function addEmptyColumn(selector) {
    if (selector === undefined) throw "Undefined selector.";
    var table = $("" + selector)

        table.find("thead tr").append(createHeaderElement(selector));
        var rows = table.find("tbody tr").not(".empty-row");
        for(var i = 0; i < rows.length; i++) {
            $(rows[i]).append(wrapWith("td", createRecordInputValue()));    
        }
}

function removeColumn(selector, columnId) {
    if (confirm("Are your sure you want to remove whole columne?") === true) {
        var headers = $("" + selector).find("thead tr th");
        var index = 0;  
        for(var i = 0; i < headers.length; i++) {
            if ($(headers[i]).data("column-id") == columnId) {
                index = i;
                break;
            }    
        }
        $(headers[i]).remove();
        var columns = $("" + selector).find("tbody tr");
        for(var i = 0; i < columns.length; i++) {
            $($(columns[i]).find("td")[index]).remove();
        }    
    }           
}

function createHeaderElement(selector) {
    if (selector === undefined) throw "Undefined selector.";
    var columnId = generateColumnId(selector);
    var $th = $("<th></th>", {"data-column-id": String(columnId)});
    $("<span></span>", {
        "class": "timerange",
        "text": "0"
    }).appendTo($th);
    $("<span> months ended on </span>").appendTo($th);
    $("<span></span>", {
        "class": "timestamp",
        "text": "0001-01-01"
    }).appendTo($th);
    $("<span> </span>").appendTo($th);
    $("<a></a>", {
        "href": "#",
        "data-toggle": "modal",
        "data-target": "#column-editor",
        "html": "<span class='glyphicon glyphicon-edit'></span>"
    }).appendTo($th);
    $("<a></a>", {
        "href": "javascript:void(0);",
        "onclick": "removeColumn('" + selector + "', " + columnId + ")",
        "html": "<span class='glyphicon glyphicon-remove'></span>"
    }).appendTo($th);            
    return $th;
}

function generateColumnId(selector) {
    if (selector === undefined) throw "Undefined Selector.";
    var maxColumnId = Math.max.apply(null, $("" + selector).find("thead tr th").map(function() {
        return $(this).data("column-id"); 
    }));
    return maxColumnId + 1;
}


function createNewRecordRow(numberOfValueInputs, attributes) {
    if (numberOfValueInputs === undefined) {
        throw "Undefined number of columns with inputs for values.";
    }
    if (attributes === undefined) attributes = {};

    var defaultAttributes = {
        "class": "record-row ui-widget-content"
    };
    $.extend(defaultAttributes, attributes);
    var $row = $("<tr></tr>", defaultAttributes);

    $row.append(
        wrapWith("td", 
            createRecordRemoveButton(),
            {"class": "no-right-padding"}
        )
    );
    $row.append(
        wrapWith("td", 
            createRecordScrollToRowButton(), 
            {"class": "no-left-padding"}
        )
    );  
    $row.append(wrapWith(
        "td", $("<select></select>", {"class": "rtype-selection"})
    ));
    $row.append(wrapWith(
        "td", $("<select></select>", {"class": "units-selection"})
    ));
    for (var i = 0; i < numberOfValueInputs; i++) {
        $row.append(wrapWith("td", createRecordInputValue()));
    }

    // Remove comment if you want to make rows draggable.
    // $row.makeDraggable().makeDroppable();

    return $row;
}

function populateRowWithData(row, rtypes, data) {
    if (data === undefined) data = {"type": undefined, "values": []}

    var valueInputs = row.find(".record-value");
    for (var i = 0; i < valueInputs.length; i++) {
        var value = 0;
        if (data.values.length  > i) {
            value = data.values[i];
        }
        $(valueInputs[i]).val(value);
    }

    row.find(".rtype-selection").applySelect2({
        data: rtypes, text: "name"
    });
    if (data.type !== undefined) {
        row.find(".rtype-selection").val(String(data.type)).trigger("change");
    }
}

function bindRecordToRow(row, recordType) {
    row.attr("data-row-name", recordType);
    row.find(".record-name").empty()
    row.find(".record-name").append(createLinkToRecord(recordType));
}

function createLinkToRecord(recordType) {
    return wrapWith("a",
        $("<span>" + recordType + "</span>"),
        { 
            "href": "javascript:void(0);",
            "onclick": "focusOnRecord('*[data-record-name=\"" + recordType + "\"]');"
        }
    );
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

function createRecordRemoveButton() {
    return wrapWith("button",
        $("<span></span>", {"class": "glyphicon glyphicon-remove"}),
        {
            "class": "btn btn-danger btn-xs record-remove-btn",
            "type": "button"
        }
    ); 
}

function createRecordScrollToRowButton() {
    return wrapWith("button",
        $("<span></span>", {"class": "glyphicon glyphicon-arrow-up"}),
        {
            "class": "btn btn-primary btn-xs btn-to-row",
            "type": "button"
        }
    );    
}


function focusOnRecord(selector, time) {
    if (time === undefined) time = 500;
    var element = $(selector);
    if (element.length == 0) {
        alert("There is no coressponding record. Probably it was removed.");
    } else {
        $(selector).addClass("backgroundAnimated");
        $("html, body").animate({
            scrollTop: $(selector).offset().top
        }, time);
    }
}

function focusOnRow(selector) {
    var element = $(selector);
    if (element.length == 0) {
        alert("There is no coressponding row. Probably it was removed.");
    } else {
        scrollToRow(selector); 
        location.hash = "#report-wrapper";
        $(selector).addClass("backgroundAnimated");
    }
}

function scrollToRow(selector) {
    var toffset = $("#report-content thead").position().top;
    var $frow = $("#report-content tbody " + selector);
    var roffset = $frow.position().top;
    // $("#report-content").scrollTop(roffset - toffset);
    $("#report-content").animate({
        scrollTop: roffset - toffset
    }, 1000);
}

function createRecordTypeSelect(options, selected) {
    var $select = $("<select></select>", {"class": "rtype-selection"});
    for(var i = 0; i < options.length; i++) {
        createRecordTypeSelectOption(options[i].id, options[i].name).
        appendTo($select);
    }
    $select.val(String(selected));
    return $select;
}

function createRecordTypeSelectOption(value, name) {
    var $option = $("<option></option>", {
        "value": String(value),
        "text": name
    });
    return $option;
}

function getNumberOfColumns(selector) {
    if (selector === undefined) throw "Undefined selector.";
    return $("" + selector).find("thead th").length - FIXED_COLUMNS;
}

function createRecordInputValue(value) {
    return wrapWith("div",
        $("<input></input>", {
            "type": "text",
            "class": "form-control input-sm record-value",
            "val": (value ? value !== undefined : 0)
        })    
    );
}

function appendLastDayOfMonth(string) {
    var date = moment(string, "YYYY-MM");
    if (date.isValid()) {
        return date.endOf("month").format("YYYY-MM-DD");
    } else {
        return string;
    }
}

function createDataForExport(tables) {
    var timerange = $("#report-timerange").text();
    var timestamp = appendLastDayOfMonth($("#report-timestamp").text());
    var companyId = $("#company-select").val();

    var records = tables.map(function(tname) {
        return readRecordsFromTable(tname, companyId);
    }).reduce(function(r1, r2) {
        return r1.concat(r2);
    });

    var data = JSON.stringify({
        "timerange": timerange,
        "timestamp": timestamp,
        "company_id": companyId,
        "records": records
    });


    return data;
}

function readRecordsFromTable(selector, companyId) {
    if (companyId === undefined) companyId = null;

    var table = $(selector);
    var headers = getRecordsHeaders(table);

    var records = table.find("tbody tr:not(:first-child)").map(function(rowIndex) {
        var tds = $(this).find("td");
        var recordType = $(tds[RECORD_TYPE_COLUMN]).find("select").val();
        var uom = parseInt($(tds[UNITS_OF_MEASURE_COLUMN]).find("select").val());
        return $(this).find("td").slice(FIXED_COLUMNS).map(function(columnIndex) {
            return {
                "company_id": companyId,
                "value": parseFloat($(this).find("input").val()) * uom,
                "rtype_id": recordType,
                "timerange": parseInt(headers[columnIndex].timerange),
                "timestamp": headers[columnIndex].timestamp
            }       
        }).get();
    }).get();

    return records;
}

function switchLayout() {
    var currentStyle = $("td.content").css("white-space");
    if (currentStyle === "pre") {
        $("td.content").css("white-space", "normal");
    } else {
        $("td.content").css("white-space", "pre");   
    }
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

function createRecordForm(config) {
    if (config === undefined) config = {};
    if (config.numberOfColumns === undefined) config.numberOfColumns = 2;

    var $form = $("<form/>", {class: "form-horizontal"});

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-sm-2", "text": "Financial Item"}),
            wrapWith("div",
                createSelect([], {"class": "new-record-name"}),
                {"class": "col-sm-10"}
            )
        ], 
        {"class": "form-group"}
    ));

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-sm-2", "text": "Statement"}),  
            wrapWith("div",
                createSelect(
                    [{"name": "BLS"}, {"name": "ICS"}, {"name": "CFS"}],
                    {"class": "new-record-statement"}
                ),
                {"class": "col-sm-10"}
            )  
        ],
        {"class": "form-group"}
    ));

    var valueInputs = [];
    for(var i = 0; i < config.numberOfColumns; i++) {
        valueInputs.push(createInput({placeholder: "Column " + (i+1)}));
    }
    valueInputs.push(
        createButton(
            $("<span/>",{"class": "glyphicon glyphicon-plus"}),
            {
                "class": "btn btn-primary btn-xs",
                "click": function() {
                    var columnNo = $(this).parent().find("input").length + 1;
                    var $input = createInput({"placeholder": "Column " + columnNo});     
                    $input.insertBefore($(this));
                }
            }
        )
    );
    valueInputs.push(
        createButton(
            $("<span/>",{"class": "glyphicon glyphicon-minus"}),
            {
                "class": "btn btn-danger btn-xs",
                "click": function() {
                    var $lastInput = $(this).parent().find("input").last();
                    $lastInput.remove();
                }
            }
        )
    );

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-sm-2", "text": "Financial Data"}), 
            wrapWith("div",
                valueInputs,
                {"class": "form-inline col-sm-10"}
            ) 
        ],
        {"class": "form-group"}
    ));

    $form.append(wrapWith("div",
        wrapWith("div",
            wrapWith("div",
                [
                    createButton(
                        $("<span/>",{"text": "Add"}),
                        {
                            "class": "btn btn-sm btn-success btn-record-add",
                            "click": config.addCallback
                        }
                    ),
                    createButton(
                        $("<span/>",{"text": "Abort"}),
                        {
                            "class": "btn btn-sm btn-danger btn-record-abort",
                            "click": config.abortCallback
                        }
                    )
                ],
                {"class": "btn-toolbar"}
            ),
            {"class": "col-sm-offset-2 col-sm-10"}
        ),
        {"class": "form-group"}
    ));

    $form.find("select.new-record-name").applySelect2({
        data: config.rtypes, text: "name"
    });

    return $form;
}

function createSelect(options, attributes) {
    var $select = $("<select></select>", attributes);
    for(var i = 0; i < options.length; i++) {
        createSelectOption(options[i].id, options[i].name).
        appendTo($select);
    }
    return $select;
}

function createSelectOption(value, name) {
    var $option = $("<option></option>", {
        "value": String(value),
        "text": name
    });
    return $option;
}

function createLabel(attributes) {
    return $("<label/>", attributes);
}

function createInput(attributes) {
    var defaultAttributes = {
        type: "text", class: "form-control input-sm record-value",
        value: "0", placeholder: "Column"
    };
    $.extend(defaultAttributes, attributes);
    return $("<input/>", defaultAttributes);
}

function createButton(elements, attributes) {
    var defaultAttributes = {"type": "button"};
    if (attributes === undefined) attributes = {};
    $.extend(defaultAttributes, attributes);
    return wrapWith("button", elements, defaultAttributes);   
}

function readDataFromRecordForm(form) {
    var recordsData = {
        "type": form.find(".new-record-name :selected").val(),
        "type_name": form.find(".new-record-name :selected").text(),
        "statement": form.find(".new-record-statement :selected").text(),
        "values": 
            form.find("input.record-value").map(
                function () {
                    return $(this).val();
                }
            ).get()
    };
    return recordsData;
}

function findDuplicateRecords(table) {
    var records = table.find("tbody tr").map(function(rowIndex) {
        var tds = $(this).find("td");
        var recordType = $(tds[RECORD_TYPE_COLUMN]).find("select").find("option:selected").text();
        return recordType;
    }).get();

    var recordsCounter = {};
    for (var i = 0; i < records.length; i++) {
        if (!(records[i] in recordsCounter)) {
            recordsCounter[records[i]] = 0;
        }
        recordsCounter[records[i]] += 1;
    }

    var duplicatedRecords = [];
    for (var property in recordsCounter) {
        if (recordsCounter.hasOwnProperty(property)) {
            if (recordsCounter[property] > 1) {
                duplicatedRecords.push(property);
            }
        }
    }
    return duplicatedRecords;
}

function validateDuplicateRecords(table) {
    var records = findDuplicateRecords(table);
    return {"result": records.length === 0, "details": records};
}

function validateRecordsColumns(table) {
    var headers = getRecordsHeaders(table);
    var result = true;
    var details = headers.map(function(header, index) {
        result = result && !isNaN(header.timerange) && moment(header.timestamp).isValid();
        return {
            "timerange": !isNaN(header.timerange),
            "timestamp": moment(header.timestamp).isValid(),
            "index": index
        };
    });
    return {"result": result, "details": details};
}

function validateRecords(table) {
    var result = true;
    var columnNumbers = table.find("thead th").length;
    var details = table.find("tbody tr:not(:first-child)").map(function(index) {
        var numberOfCells = $(this).find("td").length;
        var cells = $(this).find("td:nth-child(n+" + (FIXED_COLUMNS+1) + ")").map(function(index) {
            result = result && !isNaN($(this).find("input").val());
            return {
                "value": !isNaN($(this).find("input").val()),
                "index": index
            };
        }).get();
        return {
            "rows": numberOfCells == columnNumbers,
            "cells": cells,
            "index": index,
            "rtype": $(this).find(".rtype-selection option:selected").text()
        };
    }).get();
    return {"result": result, "details": details};
}

function validateCompany() {
    var result = true;
    var companyId = $("#company-select").val();
    if (companyId === undefined || companyId === null) {
        result = false;
    }
    return {"result": result, "details": result}
}

function validateReport() {
    var timerange = $("#report-timerange").text();
    var timestamp = appendLastDayOfMonth($("#report-timestamp").text());   
    return {
        "result": !isNaN(timerange) && moment(timestamp).isValid(),
        "details": {
            "timerange": !isNaN(timerange),
            "timestamp": moment(timestamp).isValid()
        }
    }
}

function validateDataInTable(table, prefix) {
    var vals = [
        validateDuplicateRecords(table),
        validateRecordsColumns(table),
        validateRecords(table),
    ];
    var result = vals.every(function(val) { return val.result; });
    var alerts = [].concat(
        createAlertsForDuplicatedRecords(vals[0].details, prefix)
    ).concat(
        createAlertsForRecordsColumnsValidation(vals[1].details, prefix)
    ).concat(
        createAlertsForRecordsValidation(vals[2].details, prefix)
    );
    return {"result": result, "alerts": alerts};
}

function createAlertsForDuplicatedRecords(duprecords, prefix) {
    prefix = adjust_prefix(prefix);
    var alerts = [];
    var msg;
    for (var i = 0; i < duprecords.length; i++) {
        msg = prefix + duprecords[i] + " is duplicated";
        alerts.push(createAlert(msg, "danger"));
    }
    return alerts;
}

function createAlertsForRecordsColumnsValidation(validation, prefix) {
    prefix = adjust_prefix(prefix);
    var alerts = [];
    for(var i = 0; i < validation.length; i++) {
        if (!validation[i].timerange || !validation[i].timestamp) {
            var msg = prefix + "Column #" + (validation[i].index + 1) + ":";
            if (!validation[i].timerange) {
                msg += " timerange corrupted;";
            }
            if (!validation[i].timestamp) {
                msg += " timestamp corrupted;";
            }
            alerts.push(createAlert(msg, "danger"));
        }
    }
    return alerts;
}

function createAlertsForRecordsValidation(validation, prefix) {
    prefix = adjust_prefix(prefix);
    var alerts = [];
    var msg;
    for(var i = 0; i < validation.length; i++) {
        if (!validation[i].rows) {
            msg = prefix + "Row #" + (validation[i].index + 1) + ": " +
                  "different number of records";
            alerts.push(createAlert(msg, "warning"));
        }
        for(var j = 0; j < validation[i].cells.length; j++) {
            if (!validation[i].cells[j].value) {
                msg = prefix + "Row #" + (validation[i].index + 1) + " with " + validation[i].rtype + ": " +
                      "not a number in column #" + (validation[i].cells[j].index + 1);
                alerts.push(createAlert(msg, "danger"));
            }
        }
    }
    return alerts;
}

function createAlertForCompanyValidation(validation, prefix) {
    prefix = adjust_prefix(prefix);
    if (!validation) {
        var msg = prefix + "Company not identified";
        return createAlert(msg, "danger");
    }
    return null;
}

function createAlertForReportValidation(validation, prefix) {
    prefix = adjust_prefix(prefix);
    if (validation.timerange && validation.timestamp) {
        return null;
    }
    var msg = prefix + "Financial report identification:"
    if (!validation.timerange) {
        msg += " timerange corrupted;";
    }
    if (!validation.timestamp) {
        msg += " timestamp corrupted;";
    }
    return createAlert(msg, "warning");
}

function adjust_prefix(prefix) {
    if (prefix === undefined) {
        prefix = "";
    } else {
        prefix = prefix + ": ";
    }
    return prefix; 
}

function getRecordsHeaders(table) {
    var headers = table.find("thead tr th").slice(FIXED_COLUMNS).map(function() {
        return {
            "timerange": $(this).find(".timerange").text(),
            "timestamp": $(this).find(".timestamp").text()
        };
    }).get();
    return headers;
}

function createAlert(text, context) {
    if (context === undefined) context = "info";
    var alert = wrapWith("div", [
            $("<p></p>", {"text": text})
        ],
        {
            "class": "alert alert-" + context,
            "role": "alert"
        }
    );
    return alert;
}

function submitExportForm(data, validator) {
    var validation = validator();
    clearAlerts();
    if (!validation.result) {
        BootstrapDialog.alert({
            title: "Validation Data - Errors",
            message: "Validation procedure has detected serious erros. They will make impossible to upload all or part of your data into openstock database. Please correct them before uploading.",
            type: BootstrapDialog.TYPE_DANGER
        });
        showDataValidation();
        appendAlerts(validation.alerts);
        return false;
    } else {
        if (validation.alerts.length > 0) {
            if (BootstrapDialog.confirm({
                title: "Validation Data - Warnings",
                type: BootstrapDialog.TYPE_WARNING,
                message: "Validation procedure has detected some warnings. They are not danger but may point out to some inconsistency in your data which will in the end influence quality if data in openstock database.  Do you want to continue?",
                btnCancelLabel: "No, I want to inspect the warnings.",
                btnOKLabel: "Yes, export data."
            })) {
                showDataValidation();
                appendAlerts(validation.alerts);
                return false;
            }
        }
        $("#data-to-export").val(data);
        return false;
    }
}

function appendAlerts(alerts) {
    var $container = $(".data-validation-alerts");
    if (!$.isArray(alerts)) {
        $container.append(alerts);
    } else {
        for (var i = 0; i < alerts.length; i++) {
            $container.append(alerts[i]);
        }
    }
}

function clearAlerts() {
    $(".data-validation-alerts").empty();
}

function showDataValidation() {
    $(".data-validation").show();
}

function refreshReportUI() {
    var counter = $(".selector > input:checkbox:checked").length;
    if (counter > 0) {
        $("#row-remove-btn").css("display","inline-block");
        $("#stm-filter-btn").text("NONE");
        $("#stm-filter-btn").data("select-type", "NONE");
    } else {
        $("#row-remove-btn").css("display","none"); 
        $("#stm-filter-btn").text("ALL");
        $("#stm-filter-btn").data("select-type", "ALL");
    }  
}