$(document).ready(function () {
    $("#butt").click(function (event) {
        console.log("big cheese");
        
        event.preventDefault();
        var song = $("#song").val();

        $.ajax({
            type: "POST",
            url: "/predict",
            data: { song: song },
            success: function (response) {
                console.log("Success");
                console.log(response.data);
                console.log(response.recs);
                $("#hed").text(response.data);  // Update H1 with prediction
                
                $("#one").text(response.recs);
            }
        });
    });
});

function about(){
    document.getElementById("home").hidden = true;
    document.getElementById("about").hidden = false;
    
}

function home(){
    document.getElementById("about").hidden = true;
    document.getElementById("home").hidden = false;
}


