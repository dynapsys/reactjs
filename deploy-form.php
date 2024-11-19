<?php
// deploy-form.php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $domain = $_POST['domain'] ?? '';
    $cf_token = $_POST['cf_token'] ?? '';
    $deployment_type = $_POST['deployment_type'] ?? 'git';

    if ($deployment_type === 'git') {
        $source = $_POST['git_url'] ?? '';
    } else {
        $source_content = $_POST['source_content'] ?? '';
        $source = "data:application/tar+gz;base64," . base64_encode($source_content);
    }

    // Przygotowanie danych do wysłania
    $data = [
        'domain' => $domain,
        'cf_token' => $cf_token,
        'source' => $source
    ];

    // Inicjalizacja cURL
    $ch = curl_init('http://localhost:8000');
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
        :root {
            --primary-color: #0066cc;
            --error-color: #dc3545;
            --success-color: #198754;
        }

        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
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

        .deployment-type {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }

        .deployment-type label {
            margin-right: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }

        input[type="text"], input[type="url"], textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }

        textarea {
            min-height: 200px;
            font-family: monospace;
            resize: vertical;
        }

        button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            filter: brightness(110%);
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
            display: none;
        }

        .success {
            background: #d4edda;
            color: #155724;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
        }

        .loading {
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .loading::after {
            content: "";
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
<h1>React Deployment Form</h1>
<div class="container">
    <div class="form-container">
        <form id="deploymentForm" method="POST">
            <div class="deployment-type">
                <label>Typ deploymentu:</label>
                <input type="radio" id="git_type" name="deployment_type" value="git" checked>
                <label for="git_type">Git Repository</label>
                <input type="radio" id="code_type" name="deployment_type" value="code">
                <label for="code_type">Kod źródłowy</label>
            </div>

            <div class="form-group">
                <label for="domain">Domena:</label>
                <input type="text" id="domain" name="domain" value="reactjs.dynapsys.com" required>
            </div>

            <div class="form-group">
                <label for="cf_token">Cloudflare Token:</label>
                <input type="text" id="cf_token" name="cf_token" required>
            </div>

            <div id="git_section" class="form-group">
                <label for="git_url">Git URL:</label>
                <input type="url" id="git_url" name="git_url" placeholder="https://github.com/user/repo.git">
            </div>

            <div id="code_section" class="form-group hidden">
                <label for="source_content">Kod źródłowy aplikacji React:</label>
                <textarea id="source_content" name="source_content" placeholder="Wklej tutaj kod źródłowy aplikacji React"></textarea>
            </div>

            <button type="submit">Wykonaj Deployment</button>
        </form>

        <div id="loading" class="loading"></div>
        <div id="result" class="result"></div>
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
    const loading = document.getElementById('loading');
    const gitSection = document.getElementById('git_section');
    const codeSection = document.getElementById('code_section');

    // Przełączanie między typami deploymentu
    document.querySelectorAll('input[name="deployment_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'git') {
                gitSection.classList.remove('hidden');
                codeSection.classList.add('hidden');
            } else {
                gitSection.classList.add('hidden');
                codeSection.classList.remove('hidden');
            }
            updatePreview();
        });
    });

    function updatePreview() {
        const formData = new FormData(form);
        const deploymentType = formData.get('deployment_type');

        let source;
        if (deploymentType === 'git') {
            source = formData.get('git_url');
        } else {
            const sourceContent = formData.get('source_content');
            source = `data:application/tar+gz;base64,${btoa(sourceContent)}`;
        }

        const previewData = {
            domain: formData.get('domain'),
            cf_token: formData.get('cf_token'),
            source: source
        };

        preview.textContent = JSON.stringify(previewData, null, 2);
    }

    form.addEventListener('input', updatePreview);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        loading.style.display = 'flex';
        result.style.display = 'none';

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

        } catch (error) {
            result.className = 'result error';
            result.textContent = `Błąd: ${error.message}`;

        } finally {
            loading.style.display = 'none';
            result.style.display = 'block';
        }
    });

    // Inicjalizacja podglądu
    updatePreview();
</script>
</body>
</html>