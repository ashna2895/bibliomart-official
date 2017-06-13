$('.add-cart-button').on('click',function(){
    var postData = {
        book_id : $(this).attr('bookId'),
        _csrf_token : $(this).attr('csrfToken'),
        type : 'AddBook'
    }
    postCartData(postData);
});

$('.remove-cart-button').on('click',function(){
    var postData = {
        book_id : $(this).attr('bookId'),
        _csrf_token : $(this).attr('csrfToken'),
        type : 'RemoveBook'
    }
    postCartData(postData);
});

$('.place-order-button').on('click',function(){
    var postData = {
        _csrf_token : $(this).attr('csrfToken'),
        type : 'PlaceOrder'
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
