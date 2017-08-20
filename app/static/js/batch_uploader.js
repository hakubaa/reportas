$(document).ready(function() {

    $("select.record-uom").bindUnitsOfMeasure();
    $("#company-select").applySelect2();
    $(".record-row").makeDraggable().makeDroppable();

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
                $self.closest("tr").find("span.record-rtype-select-msg").remove();

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

    activateFocusOnInputs("#identified-records");

    $(document).on("click", ".data-export-btn", function(event) {
        var data = createDataForExport(["#identified-records"], rtypes);
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


function validateData() {
    var val_table = validateDataInTable($("#identified-records"));
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
    $row.append(wrapWith("td", createRecordRemoveButton()));
    $row.append(createRecordTypeCell());
    $row.append(createUOMCell());
    for (var i = 0; i < numberOfValueInputs; i++) {
        $row.append(createInputValueCell());
    }

    // Remove comment if you want to make rows draggable.
    $row.makeDraggable().makeDroppable();

    return $row;
}