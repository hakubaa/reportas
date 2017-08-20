$(document).ready(function() {
    $("select.record-uom").bindUnitsOfMeasure();
    $("#company-select").applySelect2();
    
    // Remove comment if you want to make rows draggable.
    // $(".record-row").makeDraggable().makeDroppable();

    $(document).on("click", ".record-remove-btn", function() {
        var $table = $(this).closest("table");
        $(this).closest("tr").remove();
        toggleTable($table);
    });

    $(document).on("click", ".record-rtype-btn", function() {
        var $self = $(this);
        var recordId = getIDforRType($self.closest("td").find(".record-rtype").text(), rtypes);
        var dialog = createRTypeSelectionDialog({
            data: rtypes, text: "name", 
            initval: recordId,
            callback: function(rtype) {
                $self.closest("td").find(".record-rtype").text(rtype.text);
                $self.closest("tr").attr("data-record-rtype", rtype.text);

            }
        });
        dialog.open();
    });

    $(document).on("click", ".time-editor-btn", function() {
        var $timerange = $(this).parent().find(".timerange");
        var $timestamp = $(this).parent().find(".timestamp");
        var dialog = createTimeSelectionDialog({
            "timerange": $timerange,
            "timestamp": $timestamp
        });
        dialog.open();
    });

    activateFocusOnInputs("#ics-table");
    activateFocusOnInputs("#bls-table");
    activateFocusOnInputs("#cfs-table");

    // Seting animation when user clisk record in rows-table
    $("tr").on( // remove class from row to enable next animation
        "webkitAnimationEnd oanimationend msAnimationEnd animationend",
        function() {
            $(this).removeClass("backgroundAnimated");
        }
    );

    // $(document).on("change", ".record-row select", function() {
    //     var recordType = $(this).find("option:selected").text();
    //     var $row = $(this).closest("tr");
    //     $row.attr("data-record-rtype", recordType);
    // });

    $(document).on("click", ".btn-to-row", function() {
        var recordType = $(this).closest("tr").attr("data-record-rtype");
        focusOnRow("*[data-row-name='" + recordType + "']");
    });

    // Config form for adding new records
    $(document).on("click", ".recordform-btn", function() {
        var $currentRow = $(this).closest("tr");
        if (!$currentRow.next().hasClass("record-form")) {
            wrapWith("tr",
                wrapWith("td",
                    createRecordForm({
                        "rtypes": rtypes,
                        "abortCallback": function() {
                            $(this).closest("tr").remove();
                        },
                        "addCallback": function() {
                            var recordsData = readDataFromRecordForm($(this).closest("form"));
                            if (recordsData.type === "NONE") {
                                alert("No item selected. Please select one of the item from the list.");
                            } else {
                                var tableSelector = "#" + recordsData.statement.toLowerCase() + "-table";

                                var recordType = recordsData.type_name;
                                var numberOfColumns = getNumberOfColumns(tableSelector);
                                if (numberOfColumns < recordsData.values.length) {
                                    for(var i = 0; i < recordsData.values.length - numberOfColumns; i++) {
                                        addEmptyColumn(tableSelector);
                                    }
                                    numberOfColumns = recordsData.values.length;
                                }
                                var $newRow = createNewRecordRow(
                                    numberOfColumns, 
                                    {"data-record-rtype": recordType}
                                );
                                populateRowWithData($newRow, rtypes, recordsData);
                                addRowToTable($(tableSelector), $newRow);
                                bindRecordToRow($currentRow, recordType);
                                $(this).closest("tr").remove();
                            }
                        }
                    }),
                    {"colspan": "100%"}
                ),
                {"class": "record-form"}
            ).insertAfter($currentRow);
        }
    });

    // Setting report-ui
    $("#row-remove-btn").click(function() {
        $("#report-content").find(".selector input:checked").each(function() {
            $(this).closest("tr").remove();
        });
    });


    $(".selector > input").change(function() {
        refreshReportUI();
    });

    $('#stm-filter-list a, #stm-filter-btn').click(
        function () {
            var stype = $(this).data("select-type");
            if (stype !== undefined) {
                // Turn off all checkboxes.
                $(".selector > input:checkbox").prop("checked", false);
                switch(stype) {
                    case "ALL":
                        $(".selector > input:checkbox").prop("checked", true);
                        break;
                    case "NONE":
                        $(".selector > input:checkbox").prop("checked", false);
                        break;
                    case "BLS":
                        $("tr[data-stm='bls']").find(".selector > input").prop("checked", true);
                        break;
                    case "ICS":
                        $("tr[data-stm='ics']").find(".selector > input").prop("checked", true);
                        break;
                    case "CFS":
                        $("tr[data-stm='cfs']").find(".selector > input").prop("checked", true);
                        break;
                }
            }
            refreshReportUI();
        }
    );

    $(document).on("click", ".data-export-btn", function(event) {
        var data = createDataForExport(["#bls-table", "#ics-table", "#cfs-table"], rtypes);
        if (data.records === undefined || data.records.length === 0) {
            BootstrapDialog.alert({
                title: "Validation Data - Errors",
                message: "Nothing to export. There are not any records in the table.",
                type: BootstrapDialog.TYPE_DANGER
            });
        } else {
            submitExportForm(JSON.stringify(data), validateData, function(result) {
                if (result) {
                    $("#export-data-form").submit();
                }
            });
        }
        event.preventDefault();
        return false;     
    });
    
    $("#report-disable-btn").change(function() {
        if ($(this).is(":checked")) {
            $("#report-data").hide();
        } else {
            $("#report-data").show();
        }
    });

});


function activateTab(tab){
    $('.nav-tabs a[href="#' + tab + '"]').tab('show');
};


function createNewRecordRow(numberOfValueInputs, attributes) {
    if (numberOfValueInputs === undefined) {
        throw "Undefined number of columns with inputs for values.";
    }
    if (attributes === undefined) attributes = {};

    var defaultAttributes = {
        "class": "record-row ui-widget-content",
        "data-record-rtype": UNDEFINED_RTYPE
    };
    $.extend(defaultAttributes, attributes);

    var $row = $("<tr></tr>", defaultAttributes);
    $row.append(
        wrapWith("td", 
            createRecordRemoveButton(),
            {"class": "no-right-padding cell-btn"}
        )
    );
    $row.append(
        wrapWith("td", 
            createRecordScrollToRowButton(), 
            {"class": "no-left-padding cell-btn"}
        )
    );  
    $row.append(createRecordTypeCell());
    $row.append(createUOMCell());
    for (var i = 0; i < numberOfValueInputs; i++) {
        $row.append(createInputValueCell());
    }

    // Remove comment if you want to make rows draggable.
    $row.makeDraggable().makeDroppable();

    return $row;
}


function validateData() {
    var val_bls = validateDataInTable($("#bls-table"), "Balance Sheet");
    var val_ics = validateDataInTable($("#ics-table"), "Income Statement");
    var val_cfs = validateDataInTable($("#cfs-table"), "Cash Flow Statement");
    var val_company = validateCompany();
    
    var result = [ val_bls, val_ics, val_cfs, val_company ].every(
        function(val) { return val.result; }
    );
    var alerts = [].concat(val_bls.alerts).concat(val_ics.alerts).concat(val_cfs.alerts);
    
    if (!$("#report-disable-btn").is(":checked")) {
        var val_report = validateReport();
        alerts.push(createAlertForReportValidation(val_report.details));
    }

    return {
        "result": result, 
        "alerts": alerts.filter(function(item) { 
            return item !== null && item !== undefined 
        })
    };
}