$('.add-cart-button').on('click',function(){
    console.log('here');
    var postData = {
        book_id : $(this).attr('bookId'),
        _csrf_token : $(this).attr('csrfToken'),
        type : 'add'
    }
    postCartData(postData);
});

var postCartData = function(postData) {
    var addCartURI = "/cart";
    $.post(addCartURI,postData).done(
        function(status){
            console.log(status);
            if(status==="Login"){
                window.location = "/login";
            }
            else{
                window.location = "/cart";
            }
        }).fail(
        function(xhr, status, error){
            $('#feedbackModalHeading').html("Sorry something went wrong.");
            $('#feedbackModalMessage').html("Please try again.");
            $('#feedbackModal').modal('show');
            setTimeout(function(){
                $('#feedbackModal').modal('hide');
            }, 3000);
        });
}
