var UNDEFINED_RTYPE = "undefined";


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
                id: "none",
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

jQuery.fn.bindUnitsOfMeasure = function(data) {
    if (data === undefined) {
        data = [
            {id: 1, text: "PLN"},
            {id: 1000, text: "k'PLN"},
            {id: 1000000, text: "m'PLN"}
        ];
    }
    $(this).applySelect2({
        data: data,
        minimumResultsForSearch: Infinity,
        placeholder: "Select units"
    });
}

$.fn.bindDatePicker = function(attributes) {
    if (attributes === undefined) attributes = {};

    var defaultAttributes = {
        autoclose: true,
        format: {
            toDisplay: function(date, format, language) {
                return moment(date).endOf("month").format("YYYY-MM-DD"); 
            },
            toValue: function(date, format, language) {
                var d = new Date(date);
                return d;
            }
        },
        minViewMode: "months",
        orientation: "top",
        startView: "months"
    };
    $.extend(defaultAttributes, attributes);

    for(var i = 0; i < this.length; i++) {
        $(this[i]).datepicker(defaultAttributes);
    }
};

//------------------------------------------------------------------------------
// Functions for tables with financial records
//------------------------------------------------------------------------------

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
            "onclick": "focusOnRecord('*[data-record-rtype=\"" + recordType + "\"]');"
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
            "type": "button", "tabindex": "-1"
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

function createCalculableCheckbox() {
    return $("<input></input>", {
        "type": "checkbox", "disabled": true, "tabindex": "-1"
    });
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


function appendLastDayOfMonth(string) {
    var date = moment(string, "YYYY-MM");
    if (date.isValid()) {
        return date.endOf("month").format("YYYY-MM-DD");
    } else {
        return string;
    }
}

function createDataForExport(rtables) {
    var timerange = $("#report-timerange").text();
    var timestamp = appendLastDayOfMonth($("#report-timestamp").text());
    var companyId = $("#company-select").val();

    if (!$.isArray(rtables)) {
        rtables = [rtables];
    }
    var records = rtables.map(function(rtab) {
        return rtab.getData(companyId); 
    }).reduce(function(r1, r2) {
        return r1.concat(r2);
    });

    return {
        "timerange": timerange,
        "timestamp": timestamp,
        "company_id": companyId,
        "records": records
    };
}


function switchLayout() {
    var currentStyle = $("td.content").css("white-space");
    if (currentStyle === "pre") {
        $("td.content").css("white-space", "normal");
    } else {
        $("td.content").css("white-space", "pre");   
    }
}


function createRecordForm(config) {
    if (config === undefined) config = {};
    if (config.numberOfColumns === undefined) config.numberOfColumns = 2;

    var $form = $("<form/>", {class: "form-horizontal"});

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-md-2 col-xs-1", "text": "Financial Item"}),
            wrapWith("div",
                createSelect([], {"class": "new-record-name", "style": "width: 100%;"}),
                {"class": "col-md-3 col-xs-3"}
            )
        ], 
        {"class": "form-group"}
    ));

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-md-2 col-xs-1", "text": "Statement"}),  
            wrapWith("div",
                createSelect(
                    [{"name": "BLS"}, {"name": "ICS"}, {"name": "CFS"}],
                    {"class": "new-record-statement", "style": "width: 100%;"}
                ),
                {"class": "col-md-1 col-xs-1"}
            )  
        ],
        {"class": "form-group"}
    ));

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-md-2 col-xs-1", "text": "Units of Measure"}),  
            wrapWith("div",
                createSelect([], {"class": "new-record-uom", "style": "width: 100%;"}),
                {"class": "col-md-1 col-xs-1"}
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
            createLabel({"class": "control-label col-md-2 col-xs-1", "text": "Financial Data"}), 
            wrapWith("div",
                valueInputs,
                {"class": "form-inline col-md-10 col-xs-11"}
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
            {"class": "col-md-offset-2 col-md-10 col-xs-offset-2 col-xs-10"}
        ),
        {"class": "form-group"}
    ));

    $form.find("select.new-record-name").applySelect2({data: config.rtypes, text: "name"});
    $form.find("select.new-record-statement").applySelect2({minimumResultsForSearch: Infinity});
    $form.find("select.new-record-uom").bindUnitsOfMeasure();

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
        // "type": form.find(".new-record-name :selected").val(),
        "rtype": form.find(".new-record-name :selected").text(),
        "statement": form.find(".new-record-statement :selected").text(),
        "uom": form.find(".new-record-uom").val(),
        "values": 
            form.find("input.record-value").map(
                function () {
                    return $(this).val();
                }
            ).get()
    };
    return recordsData;
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


function validateDataInTable(rtable, prefix) {
    var vals = [
        rtable.validateRecordsDuplication(),
        rtable.validateHeaders(),
        rtable.validateRecords(),
        rtable.validateRTypes()
    ];
    var result = vals.every(function(val) { return val.result; });
    var alerts = [].concat(
        createAlertsForDuplicatedRecords(vals[0].details, prefix)
    ).concat(
        createAlertsForRecordsColumnsValidation(vals[1].details, prefix)
    ).concat(
        createAlertsForRecordsValidation(vals[2].details, prefix)
    ).concat(
        createAlertsForRecordsTypesValidation(vals[3].details, prefix)
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
    if (validation.length === 0) {
        msg = prefix + "There are not any records in the table.";
        alerts.push(createAlert(msg, "warning"));        
    }
    return alerts;
}


function createAlertsForRecordsTypesValidation(validation, prefix) {
    prefix = adjust_prefix(prefix);
    var alerts = [];
    var msg;
    for(var i = 0; i < validation.length; i++) {
        if (validation[i].rtype === UNDEFINED_RTYPE) {
            msg = prefix + "Row #" + (validation[i].index + 1) + ": " +
                  "type of record corrupted";
            alerts.push(createAlert(msg, "danger"));
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


function submitExportForm(data, validator, callback) {
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
    } else {
        if (validation.alerts.length > 0) {
            BootstrapDialog.confirm({
                title: "Validation Data - Warnings",
                type: BootstrapDialog.TYPE_WARNING,
                message: "Validation procedure has detected some warnings. They are not danger but may point out to some inconsistency in your data which will in the end influence quality if data in openstock database.  Do you want to continue?",
                btnCancelLabel: "No, I want to inspect the warnings.",
                btnOKLabel: "Yes, export data.",
                callback: function(result) {
                    showDataValidation();
                    appendAlerts(validation.alerts);
                    if (result) {
                        $("#data-to-export").val(data); 
                    }
                    if (callback !== undefined) {
                        callback(result);
                    }
                }
            });
        }
        $("#data-to-export").val(data);
        if (callback !== undefined) {
            callback(true);
        }
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


function createTimeSelectionDialog(config) {
    if (config === undefined) config = {};
    if (config.title === undefined) config.title = "Timestamp  & Timerange Selection";

    var dialog = new BootstrapDialog({
        title: config.title,
        type: BootstrapDialog.TYPE_DEFAULT,
        message: function(dialog) {
            var $content = wrapWith("div", [
                wrapWith("div", [
                        $("<label>Timestamp</label>", {
                            "for": "timestamp-input", "class": "control-label"
                        }),
                        $("<input></input>", {
                            "type": "text", "class": "form-control input-sm",
                            "id": "timestamp-input"            
                        })
                    ],
                    {"class": "form-group"}
                ),
                wrapWith("div",[
                        $("<label>Timerange</label>", {
                            "for": "timestamp-input", "class": "control-label"
                        }),
                        $("<select></select>", {
                            "class": "form-control", "id": "timerange-input",
                            "style": "width: 100%;"
                        })
                    ],
                    {"class": "form-group"}
                )
            ]);
            var data = [
                {"id": "none", "text": "None"},
                {"id": 0, "text": "0"},
                {"id": 3, "text": "3"},
                {"id": 6, "text": "6"},
                {"id": 9, "text": "9"},
                {"id": 12, "text": "12"}
            ];

            var $timerangeInput = $content.find("#timerange-input");
            var $timestampInput = $content.find("#timestamp-input");

            $timerangeInput.applySelect2({"data": data});
            $timestampInput.bindDatePicker({orientation: "bottom"});

            // update inputs with current values
            if (config.timestamp !== undefined) {
                var timestamp = moment(config.timestamp.text(), "YYYY-MM");
                if (timestamp != null && timestamp.isValid()) {
                    $timestampInput.val(timestamp.format("YYYY-MM"));
                } else {
                    $timestampInput.val("");    
                }
            }
            if (config.timerange !== undefined) {
                $timerangeInput.val(config.timerange.text()).trigger("change");
            }

            return $content;
        },
        buttons: [
            {
                label: "Ok",
                cssClass: "btn-sm btn-success",
                action: function(dialog) {
                    var $timerangeInput = dialog.getModalContent().find("#timerange-input");
                    var $timestampInput = dialog.getModalContent().find("#timestamp-input");

                    dialog.close();

                    if (config.timerange !== undefined) {
                        config.timerange.text($timerangeInput.find(":selected").val());
                    }
                    if (config.timestamp !== undefined) {
                        var timestamp = $timestampInput.val();
                        if (timestamp !== "") {
                            config.timestamp.text(timestamp);
                        }    
                    }
                }
            },
            {
                label: "Abort",
                cssClass: "btn-sm btn-danger",
                action: function(dialog){
                    dialog.close();
                }
            }
        ]

    });
    return dialog;
}


function createRTypeSelectionDialog(config) {
    if (config === undefined) config = {};
    if (config.title === undefined) config.title = "Record Type Selection";

    var dialog = new BootstrapDialog({
        title: config.title,
        type: BootstrapDialog.TYPE_DEFAULT,
        message: function(dialog) {
            var $select = $("<select style='width: 100%'></select>");
            var $content = wrapWith("div", $select);
            $select.applySelect2({
                data: config.data, text: config.text,
                dropdownParent: dialog.getModal()
            });
            if (config.initval !== undefined) {
                $select.val(config.initval).trigger("change");
            }
            return $content;
        },
        buttons: [
            {
                label: "Ok",
                cssClass: "btn-sm btn-success",
                action: function(dialog) {
                    if (config.callback) {
                        var $select = dialog.getModalContent().find("select");
                        dialog.close();
                        config.callback({
                            value: $select.val(),
                            text: $select.find("option:selected").text()
                        });
                    }
                }
            },
            {
                label: "Abort",
                cssClass: "btn-sm btn-danger",
                action: function(dialog){
                    dialog.close();
                }
            }
        ]
    });
    return dialog;
}