/**
 * Send XMLHttpRequest for identification of items.
 * @param {Object} options 
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
 * @param {Object} options 
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