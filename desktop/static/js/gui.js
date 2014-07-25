$(document).ready(function () {

    // display loading screen for 200 ms
    $('#loading_page').fadeOut(200);

    // fullPage.js configuration
    $('#fullpage').fullpage({
        verticalCentered: true,
        resize: false,
        keyboardScrolling: true
    });
    $.fn.fullpage.setAllowScrolling(false);

    // update progress bars in function of python backend progress
//			setInterval(function(){
//				Sijax.request('set_progress');
//			}, 3000);

    // start upload pipeline
    $('#upload_form').bind('submit', function () {
        Sijax.request('start_upload', [$('#dir_to_upload_path').val(), $('#passphrase_field').val()]);

        // modify upload button
        $("#upload_button").prop("disabled", true);
        $("#upload_spinner").removeClass("fa-cloud-upload").addClass("fa-spinner fa-spin");
        $("#upload_txt").html(" Uploading…");

        //Prevent the form from being submitted
        return false;
    });

    // start download pipeline
    $('#download_form').bind('submit', function () {
        Sijax.request('start_download', [$('#archive_id').val(), $('#save_path').val(),
            $('#decrypt_passphrase_field').val()]);

        // modify upload button
        $("#download_button").prop("disabled", true);
        $("#download_spinner").removeClass("fa-cloud-download").addClass("fa-spinner fa-spin");
        $("#download_txt").html(" Downloading…");

        //Prevent the form from being submitted
        return false;
    });

    // open file dialog to choose dir to upload
    $('#choose_dir_to_upload_btn').click(function () {
        Sijax.request('choose_dir_to_upload');
    });


    ////////////////// Settings Dialog //////////////////
    // Check if public/private keys are loaded on app startup
    // Check if a settings.json file exists and loads settings
    // Adjust settings dialog accordingly
    Sijax.request('check_settings');


    // Load hostkey
    $('#load_hostkey_btn').click(function () {
        Sijax.request('get_hostkey_fingerprint', [$('#hostname_field').val()]);
    });

    // Close hostkey alert
    $('#close_hostkey_alert_btn').click(function () {
        $('#hostkey_alert').hide();
        $('#load_hostkey_btn').show();
        $('#hostkey_alert > h4').html('Please verify the authenticity of host&nbsp;');
        $('#hostkey_alert > span:eq(0)').html('The authenticity of host&nbsp;');
        $('#hostkey_alert > span:eq(1)').html('RSA key fingerprint is&nbsp;');
    });

    // open file dialog to choose save path for generated public key
    $('#public_key_save_path_btn').click(function () {
        Sijax.request('choose_public_key_save_path');
    });

    // Generate public/private key pair
    $('#generate_keys_btn').click(function () {
        Sijax.request('generate_keys', [$('#public_key_save_path').val()]);

        // modify #generate_keys_btn if public_key_save_path field is not empty
        if ($('#public_key_save_path').val().length != 0) {
            $("#generate_keys_btn").prop("disabled", true).html(
                "<span class='fa fa-spinner fa-spin'></span> Generating Keys..."
            );
        }
    });

    // Save hostname and username
    $("#save_settings").click(function () {
        Sijax.request('save_settings', [$('#hostname_field').val(), $('#username_field').val()]);
    });

    ////////////////// End Settings Dialog //////////////////

    // select text on focus
    $("#upload_id").focus(
        function () {
            $(this).select();
        }
    )
        .mouseup(
        function (e) {
            e.preventDefault();
        }
    );

    // main_menu navigation buttons control
    $("#main_menu_download_btn").click(function () {
        $.fn.fullpage.moveSectionDown();
    });

    $("#main_menu_upload_btn").click(function () {
        $.fn.fullpage.moveSectionUp();
    });

    // return to main_menu buttons control
    $(".return_to_main_menu_btn").click(function () {
        $.fn.fullpage.moveTo(3);
    });


    // // modify upload icon when clicked
    // $("#upload_button").click(function() {
    // 	//$("#upload_button").removeClass("btn-default").addClass("btn-success").prop("disabled", true);
    // 	$("#upload_spinner").removeClass("fa-cloud-upload").addClass("fa-spinner fa-spin");
    // 	$("#upload_txt").html(" Uploading…");
    // });
});