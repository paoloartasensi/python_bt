package com.chileaf.cl831.sample.dfu;

import android.app.Dialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.DialogFragment;
import com.chileaf.cl831.sample.R;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes4.dex */
public class PermissionRationaleFragment extends DialogFragment {
    private static final String ARG_PERMISSION = "ARG_PERMISSION";
    private static final String ARG_TEXT = "ARG_TEXT";
    private PermissionDialogListener mListener;

    public interface PermissionDialogListener {
        void onRequestPermission(final String permission);
    }

    /* JADX WARN: Multi-variable type inference failed */
    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onAttach(final Context context) {
        super.onAttach(context);
        if (context instanceof PermissionDialogListener) {
            this.mListener = (PermissionDialogListener) context;
            return;
        }
        throw new IllegalArgumentException("The parent activity must impelemnt PermissionDialogListener");
    }

    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onDetach() {
        super.onDetach();
        this.mListener = null;
    }

    public static PermissionRationaleFragment getInstance(final int aboutResId, final String permission) {
        PermissionRationaleFragment fragment = new PermissionRationaleFragment();
        Bundle args = new Bundle();
        args.putInt(ARG_TEXT, aboutResId);
        args.putString(ARG_PERMISSION, permission);
        fragment.setArguments(args);
        return fragment;
    }

    @Override // androidx.fragment.app.DialogFragment
    public Dialog onCreateDialog(final Bundle savedInstanceState) {
        final Bundle args = getArguments();
        StringBuilder text = new StringBuilder(getString(args.getInt(ARG_TEXT)));
        return new AlertDialog.Builder(getActivity()).setTitle(R.string.permission_required).setMessage(text).setNegativeButton(R.string.f5no, (DialogInterface.OnClickListener) null).setPositiveButton(R.string.yes, new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$PermissionRationaleFragment$KDkNsciNFxcxnNOi4FJk8hYNRUg
            @Override // android.content.DialogInterface.OnClickListener
            public final void onClick(DialogInterface dialogInterface, int i) {
                this.f$0.lambda$onCreateDialog$0$PermissionRationaleFragment(args, dialogInterface, i);
            }
        }).create();
    }

    public /* synthetic */ void lambda$onCreateDialog$0$PermissionRationaleFragment(Bundle args, DialogInterface dialog, int which) {
        this.mListener.onRequestPermission(args.getString(ARG_PERMISSION));
    }
}
