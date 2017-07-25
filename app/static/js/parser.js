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

function switchLayout() {
    var currentStyle = $("td.content").css("white-space");
    if (currentStyle === "pre") {
        $("td.content").css("white-space", "normal");
    } else {
        $("td.content").css("white-space", "pre");   
    }
}

function scrollToRecords(selector) {
    var toffset = $("#report-content thead").position().top;
    var $frow = $("#report-content tbody tr." + selector);
    var roffset = $frow.position().top;
    $("#report-content").scrollTop(roffset - toffset);
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

function createRecordForm(rtypes, numberOfColumns) {
    if (numberOfColumns === undefined) numberOfColumns = 2;

    var $form = $("<form/>", {class: "form-horizontal"});

    $form.append(wrapWith("div",
        [
            createLabel({"class": "control-label col-sm-2", "text": "Financial Item"}),
            wrapWith("div",
                createSelect(rtypes, {"class": "rtype-selection", "id": "new-record-name"}),
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
                    {"id": "new-record-statement"}
                ),
                {"class": "col-sm-10"}
            )  
        ],
        {"class": "form-group"}
    ));

    var valueInputs = [];
    for(var i = 0; i < numberOfColumns; i++) {
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
                        {"class": "btn btn-sm btn-success btn-record-add"}
                    ),
                    createButton(
                        $("<span/>",{"text": "Abort"}),
                        {"class": "btn btn-sm btn-danger btn-record-abort"}
                    )
                ],
                {"class": "btn-toolbar"}
            ),
            {"class": "col-sm-offset-2 col-sm-10"}
        ),
        {"class": "form-group"}
    ));

    $form.applySelect2();

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