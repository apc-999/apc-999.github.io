function showError(errorMessage) {
    document.getElementById('errorMessage').innerText = "ERROR!!!!!!!\n" + errorMessage;
    $('#errorModal').modal('show');  // Trigger the modal
}
