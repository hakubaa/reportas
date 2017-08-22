$(document).ready(function() {

    $("select.record-uom").bindUnitsOfMeasure();
    $("#company-select").applySelect2();

    $("#report-disable-btn").change(function() {
        if ($(this).is(":checked")) {
            $("#report-data").hide();
        } else {
            $("#report-data").show();
        }
    });

    $(document).on("click", ".report-time-editor-btn", function() {
        var $timerange = $(this).parent().find(".timerange");
        var $timestamp = $(this).parent().find(".timestamp");
        var dialog = createTimeSelectionDialog({
            "timerange": $timerange,
            "timestamp": $timestamp
        });
        dialog.open();
    });

    rtab.config("rtypes", rtypes);
    rtab.config("columns", [ 
        {
            "factory_method": createRecordRemoveButton,
            "attributes": {"class": "no-right-padding cell-btn"}
        }, 
        {
            "factory_method": createRecordScrollToRowButton,
            "attributes": {"class": "no-left-padding cell-btn"}
        }
    ]);
    rtab.bindEvents("#identified-records", rtypes);

    // Seting animation when user clisk record in rows-table
    $("tr").on( // remove class from row to enable next animation
        "webkitAnimationEnd oanimationend msAnimationEnd animationend",
        function() {
            $(this).removeClass("backgroundAnimated");
        }
    );

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
                            if (recordsData.rtype === "NONE") {
                                alert("No item selected. Please select one of the item from the list.");
                            } else {
                                var numberOfColumns = getNumberOfColumns("#identified-records");
                                if (numberOfColumns < recordsData.values.length) {
                                    for(var i = 0; i < recordsData.values.length - numberOfColumns; i++) {
                                        addEmptyColumn("#identified-records");
                                    }
                                    numberOfColumns = recordsData.values.length;
                                }
                                var $newRow = createNewRecordRow(
                                    numberOfColumns, 
                                    {"data-record-rtype": recordsData.rtype}
                                );
                                $newRow.find(".record-uom").bindUnitsOfMeasure();
                                populateRowWithData($newRow, recordsData);
                                addRowToTable($("#identified-records"), $newRow);
                                bindRecordToRow($currentRow, recordsData.rtype);
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
    
});


function addEmptyRow(selector) {
    rtab.bind(selector).addRow();
}


function addEmptyColumn(selector) {
    rtab.bind(selector).addColumn();
}


function exportData() {
    var data = createDataForExport(rtab.bind("#identified-records"));
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
    return false;
}


function validateData() {
    var val_table = validateDataInTable(rtab.bind("#identified-records"));
    var alerts = val_table.alerts;

    var val_company = validateCompany();
    alerts.push(createAlertForCompanyValidation(val_company.details));

    if (!$("#report-disable-btn").is(":checked")) {
        var val_report = validateReport();
        alerts.push(createAlertForReportValidation(val_report.details));
    }

    return {
        "result": val_table.result && val_company.result, 
        "alerts": alerts.filter(function(item) { 
            return item !== null && item !== undefined 
        })
    };
}