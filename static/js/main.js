$(document).ready(function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Register page: send verification code
    if ($('#sendCodeBtn').length) {
        $('#sendCodeBtn').click(function(event) {
            event.preventDefault();
            var email = $('#email').val().trim();
            if (!email) {
                alert('Please enter email address');
                return;
            }

            var button = $(this);
            button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Sending...');

            $.ajax({
                url: '/send-verification',
                method: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify({email: email}),
                dataType: 'json',
                success: function(response) {
                    if (response && response.success) {
                        alert('✓ Verification code sent!\nPlease check your email and enter the 6-digit code below.');
                        $('#verificationCode').focus();
                    } else {
                        alert((response && response.message) || 'Error sending code');
                    }
                },
                error: function(xhr) {
                    var errMsg = 'Error sending code';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errMsg = xhr.responseJSON.message;
                    } else if (xhr.responseText) {
                        errMsg = xhr.responseText;
                    }
                    alert(errMsg);
                },
                complete: function() {
                    button.prop('disabled', false).html('<i class="fas fa-paper-plane"></i> Send Code');
                }
            });
        });
    }

    // Ensure normal login/register submit buttons trigger the form submit reliably.
    // $('#loginBtn, #registerBtn').on('click', function(event) {
    //     var form = $(this).closest('form')[0];
    //     if (!form) {
    //         return;
    //     }

    //     event.preventDefault();

    //     if (typeof form.checkValidity === 'function' && !form.checkValidity()) {
    //         if (typeof form.reportValidity === 'function') {
    //             form.reportValidity();
    //         }
    //         return;
    //     }

    //     if (typeof form.requestSubmit === 'function') {
    //         form.requestSubmit();
    //     } else {
    //         form.submit();
    //     }
    // });

    function setTheme(mode) {
        if (mode === 'dark') {
            $('body').addClass('dark-mode');
            $('#modeToggle i').removeClass('fa-moon').addClass('fa-sun');
            $('#modeToggle .mode-label').text('Light');
        } else {
            $('body').removeClass('dark-mode');
            $('#modeToggle i').removeClass('fa-sun').addClass('fa-moon');
            $('#modeToggle .mode-label').text('Dark');
        }
        localStorage.setItem('theme', mode);
    }

    $('#modeToggle').on('click', function() {
        var current = $('body').hasClass('dark-mode') ? 'dark' : 'light';
        setTheme(current === 'dark' ? 'light' : 'dark');
    });

    var savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
});
