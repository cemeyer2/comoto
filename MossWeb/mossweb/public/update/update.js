
//script to update comoto to latest repository revision
//cemeyer2 4/18/12, much code borrowed from viz, needs to be refactored

var popupStatusUpdate = 0;

var update = function(){
	var url = "/update/update";
	var hostname = window.location.hostname;
	if(hostname === "comoto.cs.illinois.edu") {
		url = "/comoto"+url;
	}
	
	reportLoadingStatusUpdate("Updating CoMoTo...");
	showLoadingPopup();
	$.ajax({
        url:url,
        data:{},
        type:'POST',
        dataType:'text',
        error:function (errorData) {
            //the update should fail due to a proxy error
            function reload() {
            	hideLoadingPopup();
    			window.location.reload(); 
			}
    		setTimeout(reload, 20000);
        },
        success:function (data) {
			function reload() {
				hideLoadingPopup();
    			window.location.reload(); 
			}
    		setTimeout(reload, 20000);
        }
    });
}

/**
 * Centers the loading popup
 */
function centerLoadingPopup(){

    // Get the dimensions
    var popupHeight = $("#loadingPopup").height();
    var popupWidth = $("#loadingPopup").width();

    // Center & size popup
    $("#loadingPopupUpdate").css({
        "position": "absolute",
        "top": window.innerHeight/2-popupHeight/2,
        "left": window.innerWidth/2-popupWidth/2
    });
    $("#backgroundPopupUpdate").css({
        "width": window.innerWidth,
        "height": window.innerHeight
    });
}

/**
 * Show loading underway
 */
function showLoadingPopup() {

    // Set the popup's text
    centerLoadingPopup();

    // If the popup's not displayed, fade it in
    if(popupStatusUpdate === 0) {
        $("#preloadMessageUpdate").fadeOut("fast");
        $("#backgroundPopupUpdate").fadeIn("fast");
        $("#loadingPopupUpdate").fadeIn("fast");
        popupStatusUpdate = 1;
    }
}

/**
 * Hide the loading progess display
 */
function hideLoadingPopup() {
    // If the popup's displayed, fade it out
    if(popupStatusUpdate === 1) {
        $("#backgroundPopupUpdate").fadeOut("fast");
        $("#loadingPopupUpdate").fadeOut("fast");
        popupStatusUpdate = 0;
    }
}

/**
 * Show the current loading status
 */
function reportLoadingStatusUpdate(message) {
    $("#loadingErrorBoxUpdate").hide();
    $("#okButtonUpdate").hide();
    $("#loadingStatusBoxUpdate").show();
    $("#loadingStatusUpdate").html(message);
}