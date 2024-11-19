<?php
// deploy-form.php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $domain = $_POST['domain'] ?? '';
    $cf_token = $_POST['cf_token'] ?? '';
    $source_content = $_POST['source_content'] ?? '';

    // Konwersja do base64
    $base64_content = base64_encode($source_content);

    // Przygotowanie danych do wysłania
    $data = [
        'domain' => $domain,
        'cf_token' => $cf_token,
        'source' => "data:application/tar+gz;base64," . $base64_content
    ];

    // Inicjalizacja cURL
    $ch = curl_init('http://reactjs.dynapsys.com:8000');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    // Wykonanie żądania
    $response = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    // Przygotowanie odpowiedzi
    $result = [
        'success' => $status === 200,
        'response' => $response,
        'status' => $status
    ];

    // Jeśli to żądanie AJAX, zwróć JSON
    if (!empty($_SERVER['HTTP_X_REQUESTED_WITH']) &&
        strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest') {
        header('Content-Type: application/json');
        echo json_encode($result);
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React Deployment Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .form-container, .preview-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        textarea {
            min-height: 200px;
            font-family: monospace;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        #preview {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
<h1>React Deployment Form</h1>
<div class="container">
    <div class="form-container">
        <form id="deploymentForm" method="POST">
            <div class="form-group">
                <label for="domain">Domena:</label>
                <input type="text" id="domain" name="domain" value="reactjs.dynapsys.com" required>
            </div>

            <div class="form-group">
                <label for="cf_token">Cloudflare Token:</label>
                <input type="text" id="cf_token" name="cf_token" required>
            </div>

            <div class="form-group">
                <label for="source_content">Zawartość aplikacji React:</label>
                <textarea id="source_content" name="source_content" required></textarea>
            </div>

            <button type="submit">Wykonaj Deployment</button>
        </form>

        <div id="result" class="result" style="display: none;"></div>
    </div>

    <div class="preview-container">
        <h2>Podgląd żądania:</h2>
        <div id="preview"></div>
    </div>
</div>

<script>
    const form = document.getElementById('deploymentForm');
    const preview = document.getElementById('preview');
    const result = document.getElementById('result');

    function updatePreview() {
        const formData = new FormData(form);
        const sourceContent = formData.get('source_content');
        const base64Content = btoa(sourceContent);

        const previewData = {
            domain: formData.get('domain'),
            cf_token: formData.get('cf_token'),
            source: `data:application/tar+gz;base64,${base64Content}`
        };

        preview.textContent = JSON.stringify(previewData, null, 2);
    }

    form.addEventListener('input', updatePreview);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('', {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            result.className = 'result ' + (data.success ? 'success' : 'error');
            result.textContent = data.success ?
                'Deployment wykonany pomyślnie!' :
                `Błąd: ${data.response}`;
            result.style.display = 'block';

        } catch (error) {
            result.className = 'result error';
            result.textContent = `Błąd: ${error.message}`;
            result.style.display = 'block';
        }
    });

    // Inicjalizacja podglądu
    updatePreview();
</script>
</body>
</html>