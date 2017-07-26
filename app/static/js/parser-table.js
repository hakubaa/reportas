var FIXED_COLUMNS = 2;
var RECORD_TYPE_COLUMN = 1;

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

jQuery.fn.applySelect2 = function() {
    for(var i = 0; i < this.length; i++) {
        $(this[i]).find("select").select2({
        dropdownAutoWidth: true,
            placeholder: {
                id: "-1",
                text: "Select an option"
            }
        });
    }
}

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

function addRow(selector, rtypes, data) {
    if (selector === undefined) throw "Undefined selector.";
    var numberOfColumns = getNumberOfColumns(selector);
    $("" + selector).find("tbody").append(createNewRow(numberOfColumns, rtypes, data));
    refreshSelects(selector);
}

function addColumn(selector) {
    if (selector === undefined) throw "Undefined selector.";
    var table = $("" + selector)
    table.find("thead tr").append(createHeaderElement(selector));
    var rows = table.find("tbody tr");
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

function refreshSelects(selector) {
    if (selector === undefined) selector = "*";
    $(selector).find(".rtype-selection").select2({
        dropdownAutoWidth: true,
        placeholder: {
            id: "-1",
            text: "Select an option"
        }
    });
}

function createHeaderElement(selector) {
    if (selector === undefined) throw "Undefined selector.";
    var columnId = generateColumnId(selector);
    var $th = $("<th></th>", {"data-column-id": String(columnId)});
    $("<span></span>", {
        "class": "column-timerange",
        "text": "0"
    }).appendTo($th);
    $("<span> months ended on </span>").appendTo($th);
    $("<span></span>", {
        "class": "column-timestamp",
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

function createNewRow(numberOfColumns, rtypes, data) {
    if (numberOfColumns === undefined) throw "Undefined number of columns.";
    if (data === undefined) data = {"type": undefined, "values": []}
    var $row = $("<tr></tr>", {
        "class": "record-row ui-widget-content"
    });
    var value; 
    $row.append(wrapWith("td", createRecordRemoveButton()));
    $row.append(wrapWith("td", createRecordTypeSelect(rtypes, data.type)));
    for (var i = 0; i < numberOfColumns; i++) {
        if (i < data.values.length) {
            value = data.values[i];
        } else {
            value = 0;
        }
        $row.append(wrapWith("td", createRecordInputValue(value)));
    }
    $row.makeDraggable().makeDroppable();
    return $row;
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
    var $button = $("<button type='button'/>").attr({
        "class": "btn btn-danger btn-xs record-remove-btn"
    });
    $("<span></span>", {
        "class": "glyphicon glyphicon-remove"
    }).appendTo($button);
    return $button;
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
    var $tableRows = $("" + selector).find("thead tr");
    var maxNumberOfCells = Math.max.apply(null, $tableRows.map(function() {
        return $(this).find("th").length - FIXED_COLUMNS;
    }).get());
    return maxNumberOfCells;
}

function createRecordInputValue(value) {
    if (value === undefined) value = 0;
    var $div = $("<div></div>", {"class": "form-group"});
    $("<input></input>", {
        "type": "text",
        "class": "form-control input-sm",
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