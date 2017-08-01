var FIXED_COLUMNS = 3;
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

jQuery.fn.applySelect2 = function(data, text) {
    var attributes = {
        dropdownAutoWidth: true,
            placeholder: {
                id: "-1",
                text: "Select an option",
            }
    };
    if (data !== undefined) {
        attributes.data = data;
        if (text !== undefined) {
            data = $.map(rtypes, function (obj) {
                obj.text = obj.text || obj[text]; 
                return obj;
            });
            attributes.data = data;
        }
    }
    for(var i = 0; i < this.length; i++) {
        $(this[i]).select2(attributes);
        if (data !== undefined) {
            var initSelected = $(this[i]).data("init-selected");
            if (initSelected) {
                var items = $.grep(data, function(obj) { 
                    return (obj.text == initSelected); 
                });
                if (items.length > 0) {
                    $(this[i]).val(String(items[0].id)).trigger("change");
                }
            }
        }
    }
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
    $newRow.find(".rtype-selection").applySelect2(rtypes, text="name");
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

// function refreshSelects(selector) {
//     if (selector === undefined) selector = "*";
//     $(selector).find(".rtype-selection").select2({
//         dropdownAutoWidth: true,
//         placeholder: {
//             id: "-1",
//             text: "Select an option"
//         }
//     });
// }

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
    for (var i = 0; i < numberOfValueInputs; i++) {
        $row.append(wrapWith("td", createRecordInputValue()));
    }

    $row.makeDraggable().makeDroppable();

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

    row.find(".rtype-selection").applySelect2(rtypes, text="name");
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
    if (value === undefined) value = 0;
    var $div = $("<div></div>", {"class": "form-group"});
    $("<input></input>", {
        "type": "text",
        "class": "form-control input-sm record-value",
        "val": value
    }).appendTo($div);
    return $div;
}

function createDataForExport() {
    var timerange = $("#report-timerange").text();
    var timestamp = $("#report-timestamp").text();
    var companyId = $("#company-id").data("company-id");

    var blsRecords = readRecordsFromTable("#bls-table", companyId);
    var icsRecords = readRecordsFromTable("#ics-table", companyId);
    var cfsRecords = readRecordsFromTable("#cfs-table", companyId);

    var data = JSON.stringify({
        "timerange": timerange,
        "timestamp": timestamp,
        "company_id": companyId,
        "records": blsRecords.concat(icsRecords, cfsRecords)
    });
    return data;
}

function readRecordsFromTable(selector, companyId) {
    if (companyId === undefined) companyId = null;

    var table = $(selector);
    var headers = table.find("thead tr th").slice(FIXED_COLUMNS).map(function() {
        return {
            "timerange": $(this).find(".column-timerange").text(),
            "timestamp": $(this).find(".column-timestamp").text()       
        };
    }).get();

    var records = table.find("tbody tr").map(function(rowIndex) {
        var tds = $(this).find("td");
        var recordType = $(tds[RECORD_TYPE_COLUMN]).find("select").find("option:selected").val();
        return $(this).find("td").slice(FIXED_COLUMNS).map(function(columnIndex) {
            return {
                "company_id": companyId,
                "value": parseFloat($(this).find("input").val()),
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

    $form.find("select.new-record-name").applySelect2(config.rtypes, text="name");
    // $form.find("select.new-record-statement").applySelect2();

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

function readRecordsFromTable(selector, companyId) {
    if (companyId === undefined) companyId = null;

    var table = $(selector);
    var headers = table.find("thead tr th").slice(FIXED_COLUMNS).map(function() {
        return {
            "timerange": $(this).find(".column-timerange").text(),
            "timestamp": $(this).find(".column-timestamp").text()       
        };
    }).get();

    var records = table.find("tbody tr").map(function(rowIndex) {
        var tds = $(this).find("td");
        var recordType = $(tds[RECORD_TYPE_COLUMN]).find("select").find("option:selected").val();
        return $(this).find("td").slice(FIXED_COLUMNS).map(function(columnIndex) {
            return {
                "company_id": companyId,
                "value": parseFloat($(this).find("input").val()),
                "rtype_id": recordType,
                "timerange": parseInt(headers[columnIndex].timerange),
                "timestamp": headers[columnIndex].timestamp
            }       
        }).get();
    }).get();

    return records;
}