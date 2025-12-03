package com.chileaf.cl831.sample.dfu;

import android.app.Dialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.DialogFragment;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import com.chileaf.cl831.sample.R;
import no.nordicsemi.android.dfu.DfuBaseService;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes4.dex */
public class UploadCancelFragment extends DialogFragment {
    private static final String TAG = "UploadCancelFragment";
    private CancelFragmentListener mListener;

    public interface CancelFragmentListener {
        void onCancelUpload();
    }

    public static UploadCancelFragment getInstance() {
        return new UploadCancelFragment();
    }

    /* JADX WARN: Multi-variable type inference failed */
    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onAttach(final Context context) {
        super.onAttach(context);
        try {
            this.mListener = (CancelFragmentListener) context;
        } catch (ClassCastException e) {
            Log.d(TAG, "The parent Activity must implement CancelFragmentListener interface");
        }
    }

    @Override // androidx.fragment.app.DialogFragment
    public Dialog onCreateDialog(final Bundle savedInstanceState) {
        return new AlertDialog.Builder(getActivity()).setTitle(R.string.dfu_confirmation_dialog_title).setMessage(R.string.dfu_upload_dialog_cancel_message).setCancelable(false).setPositiveButton(R.string.yes, new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$UploadCancelFragment$SHryrXgfwrd4esSmhvWRU7neXGU
            @Override // android.content.DialogInterface.OnClickListener
            public final void onClick(DialogInterface dialogInterface, int i) {
                this.f$0.lambda$onCreateDialog$0$UploadCancelFragment(dialogInterface, i);
            }
        }).setNegativeButton(R.string.f5no, new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$UploadCancelFragment$Cv9JKsrcxfk8dFOJl_Ge_eahIqA
            @Override // android.content.DialogInterface.OnClickListener
            public final void onClick(DialogInterface dialogInterface, int i) {
                dialogInterface.cancel();
            }
        }).create();
    }

    public /* synthetic */ void lambda$onCreateDialog$0$UploadCancelFragment(DialogInterface dialog, int whichButton) {
        LocalBroadcastManager manager = LocalBroadcastManager.getInstance(getActivity());
        Intent pauseAction = new Intent(DfuBaseService.BROADCAST_ACTION);
        pauseAction.putExtra(DfuBaseService.EXTRA_ACTION, 2);
        manager.sendBroadcast(pauseAction);
        this.mListener.onCancelUpload();
    }

    @Override // androidx.fragment.app.DialogFragment, android.content.DialogInterface.OnCancelListener
    public void onCancel(final DialogInterface dialog) {
        LocalBroadcastManager manager = LocalBroadcastManager.getInstance(getActivity());
        Intent pauseAction = new Intent(DfuBaseService.BROADCAST_ACTION);
        pauseAction.putExtra(DfuBaseService.EXTRA_ACTION, 1);
        manager.sendBroadcast(pauseAction);
    }
}
