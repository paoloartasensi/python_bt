package com.android.chileaf.util;

import android.os.Build;
import android.util.Log;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public final class LogUtil {
    private static final Tree DEBUG_TREE = new DebugTree();

    public static void v(String message, Object... args) {
        DEBUG_TREE.v(message, args);
    }

    public static void v(Throwable t, String message, Object... args) {
        DEBUG_TREE.v(t, message, args);
    }

    public static void v(Throwable t) {
        DEBUG_TREE.v(t);
    }

    public static void d(String message, Object... args) {
        DEBUG_TREE.d(message, args);
    }

    public static void d(Throwable t, String message, Object... args) {
        DEBUG_TREE.d(t, message, args);
    }

    public static void d(Throwable t) {
        DEBUG_TREE.d(t);
    }

    public static void i(String message, Object... args) {
        DEBUG_TREE.i(message, args);
    }

    public static void i(Throwable t, String message, Object... args) {
        DEBUG_TREE.i(t, message, args);
    }

    public static void i(Throwable t) {
        DEBUG_TREE.i(t);
    }

    public static void w(String message, Object... args) {
        DEBUG_TREE.w(message, args);
    }

    public static void w(Throwable t, String message, Object... args) {
        DEBUG_TREE.w(t, message, args);
    }

    public static void w(Throwable t) {
        DEBUG_TREE.w(t);
    }

    public static void e(String message, Object... args) {
        DEBUG_TREE.e(message, args);
    }

    public static void e(Throwable t, String message, Object... args) {
        DEBUG_TREE.e(t, message, args);
    }

    public static void e(Throwable t) {
        DEBUG_TREE.e(t);
    }

    public static void wtf(String message, Object... args) {
        DEBUG_TREE.wtf(message, args);
    }

    public static void wtf(Throwable t, String message, Object... args) {
        DEBUG_TREE.wtf(t, message, args);
    }

    public static void wtf(Throwable t) {
        DEBUG_TREE.wtf(t);
    }

    public static void log(int invoke, int priority, String message, Object... args) {
        DEBUG_TREE.log(invoke, priority, message, args);
    }

    public static void log(int priority, String message, Object... args) {
        DEBUG_TREE.log(priority, message, args);
    }

    public static void log(int priority, Throwable t, String message, Object... args) {
        DEBUG_TREE.log(priority, t, message, args);
    }

    public static void log(int priority, Throwable t) {
        DEBUG_TREE.log(priority, t);
    }

    public static Tree tag(String tag) {
        Tree tree = DEBUG_TREE;
        tree.explicitTag.set(tag);
        return tree;
    }

    public static void setDebug(boolean debug) {
        DEBUG_TREE.setDebug(debug);
    }

    private LogUtil() {
        throw new AssertionError("No instances.");
    }

    public static abstract class Tree {
        private final ThreadLocal<String> explicitTag = new ThreadLocal<>();
        private boolean isDebug;

        protected abstract void log(int priority, String tag, String message, Throwable t);

        String getTag() {
            String tag = this.explicitTag.get();
            if (tag != null) {
                this.explicitTag.remove();
            }
            return tag;
        }

        public void v(String message, Object... args) {
            prepareLog(5, 2, null, message, args);
        }

        public void v(Throwable t, String message, Object... args) {
            prepareLog(5, 2, t, message, args);
        }

        public void v(Throwable t) {
            prepareLog(5, 2, t, null, new Object[0]);
        }

        public void d(String message, Object... args) {
            prepareLog(5, 3, null, message, args);
        }

        public void d(Throwable t, String message, Object... args) {
            prepareLog(5, 3, t, message, args);
        }

        public void d(Throwable t) {
            prepareLog(5, 3, t, null, new Object[0]);
        }

        public void i(String message, Object... args) {
            prepareLog(5, 4, null, message, args);
        }

        public void i(Throwable t, String message, Object... args) {
            prepareLog(5, 4, t, message, args);
        }

        public void i(Throwable t) {
            prepareLog(5, 4, t, null, new Object[0]);
        }

        public void w(String message, Object... args) {
            prepareLog(5, 5, null, message, args);
        }

        public void w(Throwable t, String message, Object... args) {
            prepareLog(5, 5, t, message, args);
        }

        public void w(Throwable t) {
            prepareLog(5, 5, t, null, new Object[0]);
        }

        public void e(String message, Object... args) {
            prepareLog(5, 6, null, message, args);
        }

        public void e(Throwable t, String message, Object... args) {
            prepareLog(5, 6, t, message, args);
        }

        public void e(Throwable t) {
            prepareLog(5, 6, t, null, new Object[0]);
        }

        public void wtf(String message, Object... args) {
            prepareLog(5, 7, null, message, args);
        }

        public void wtf(Throwable t, String message, Object... args) {
            prepareLog(5, 7, t, message, args);
        }

        public void wtf(Throwable t) {
            prepareLog(5, 7, t, null, new Object[0]);
        }

        public void log(int invoke, int priority, String message, Object... args) {
            prepareLog(invoke, priority, null, message, args);
        }

        public void log(int priority, String message, Object... args) {
            prepareLog(5, priority, null, message, args);
        }

        public void log(int priority, Throwable t, String message, Object... args) {
            prepareLog(5, priority, t, message, args);
        }

        public void log(int priority, Throwable t) {
            prepareLog(5, priority, t, null, new Object[0]);
        }

        public void setDebug(boolean debug) {
            this.isDebug = debug;
        }

        private void prepareLog(int invoke, int priority, Throwable t, String message, Object... args) {
            if (!this.isDebug) {
                return;
            }
            if (message != null && message.length() == 0) {
                message = null;
            }
            if (message == null) {
                if (t == null) {
                    return;
                } else {
                    message = getStackTraceString(t);
                }
            } else {
                if (args != null && args.length > 0) {
                    message = formatMessage(message, args);
                }
                if (t != null) {
                    message = message + "\n" + getStackTraceString(t);
                }
            }
            String tag = null;
            String prefix = null;
            try {
                StackTraceElement stackTrace = Thread.currentThread().getStackTrace()[invoke];
                String fileName = stackTrace.getFileName();
                int lineNumber = stackTrace.getLineNumber();
                tag = fileName.substring(0, fileName.lastIndexOf("."));
                prefix = "(" + fileName + ":" + lineNumber + ") ";
            } catch (Exception e) {
                e.printStackTrace();
            }
            if (tag == null) {
                tag = getTag();
            }
            if (prefix != null) {
                message = prefix + message;
            }
            log(priority, tag, message, t);
        }

        private String formatMessage(String message, Object[] args) {
            return String.format(message, args);
        }

        private String getStackTraceString(Throwable t) {
            StringWriter sw = new StringWriter(256);
            PrintWriter pw = new PrintWriter((Writer) sw, false);
            t.printStackTrace(pw);
            pw.flush();
            return sw.toString();
        }
    }

    public static class DebugTree extends Tree {
        private static final Pattern ANONYMOUS_CLASS = Pattern.compile("(\\$\\d+)+$");
        private static final int CALL_STACK_INDEX = 5;
        private static final int MAX_LOG_LENGTH = 4000;
        private static final int MAX_TAG_LENGTH = 23;

        protected String createStackElementTag(StackTraceElement element) {
            String tag = element.getClassName();
            Matcher m = ANONYMOUS_CLASS.matcher(tag);
            if (m.find()) {
                tag = m.replaceAll("");
            }
            String tag2 = tag.substring(tag.lastIndexOf(46) + 1);
            if (tag2.length() <= 23 || Build.VERSION.SDK_INT >= 24) {
                return tag2;
            }
            return tag2.substring(0, 23);
        }

        @Override // com.android.chileaf.util.LogUtil.Tree
        final String getTag() {
            String tag = super.getTag();
            if (tag != null) {
                return tag;
            }
            StackTraceElement[] stackTrace = new Throwable().getStackTrace();
            if (stackTrace.length <= 5) {
                throw new IllegalStateException("Synthetic stacktrace didn't have enough elements: are you using proguard?");
            }
            return createStackElementTag(stackTrace[5]);
        }

        @Override // com.android.chileaf.util.LogUtil.Tree
        protected void log(int priority, String tag, String message, Throwable t) {
            if (message.length() < MAX_LOG_LENGTH) {
                if (priority == 7) {
                    Log.wtf(tag, message);
                    return;
                } else {
                    Log.println(priority, tag, message);
                    return;
                }
            }
            int i = 0;
            int length = message.length();
            while (i < length) {
                int newline = message.indexOf(10, i);
                int newline2 = newline != -1 ? newline : length;
                do {
                    int end = Math.min(newline2, i + MAX_LOG_LENGTH);
                    String part = message.substring(i, end);
                    if (priority == 7) {
                        Log.wtf(tag, part);
                    } else {
                        Log.println(priority, tag, part);
                    }
                    i = end;
                } while (i < newline2);
                i++;
            }
        }
    }
}
