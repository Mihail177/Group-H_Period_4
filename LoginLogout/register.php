<?php
// sessions, cookies, connect, file upload, hashed password, echo uploaded pictures, retrieve data from db

// db connection 
$dbHandler = null;

// variables for form validation
//làm ơn ghi đúng tên biến ở đây, không thì header không họat động được
$error = array();
$errorFlag = false;
$successFlag = false;

try {
    $dbHandler = new PDO("mysql:host=mysql;dbname=example;charset=utf8", "root", "qwerty");
} catch (Exception $ex) {
    printError($ex->getMessage());
}

function printError(String $error)
{
    echo "<h1>Please resolve the following error</h1>";
    echo "<p>" . $error . "</p>";
}

if ($_SERVER['REQUEST_METHOD'] == "POST") {
    $name = filter_input(INPUT_POST, "name");
    $email = filter_input(INPUT_POST, "email", FILTER_VALIDATE_EMAIL);
    $pass = filter_input(INPUT_POST, "password");

    if (empty($name) || empty($email) || empty($pass)) {
        $errors[] = "Please fill in the required information";
        $errorFlag = true;
    }

    if (strlen($name) < 2) {
        $errors[] = "Your name must be longer than 1 word";
        $errorFlag = true;
    }

    if (strpos($email, "@") === false) {
        $errors[] = "Your email must contain the character @";
        $errorFlag = true;
    }

    if (!$errorFlag) {
        $successFlag = true;
        $hashedPass = password_hash($pass, PASSWORD_BCRYPT);

        $insert = "INSERT INTO users(name, password, email) VALUES (?,?,?)";
        $stmt = $dbHandler->prepare($insert);
        $stmt->execute([$name, $hashedPass, $email]);
        if ($stmt->errorCode() !== '00000') {
            printError("SQL error: " . implode(',', $stmt->errorInfo()));
        }

        // Update the login page URL below
        header("Location: login.php");
        exit();
    }

    else {
        foreach ($error as $errors) {
            echo "<p>".$errors."</p>";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
</head>

<body>
                <form action="<?=$_SERVER['PHP_SELF']?>" method="post">
                    <p>
                        <label for="name">Name: </label>
                        <input type="text" name="name">
                    </p>
                    <p>
                        <label for="email">Email: </label>
                        <input type="email" name="email">
                    </p>
                    <p>
                        <label for="password">Password: </label>
                        <input type="password" name="password">
                    </p>
                    <p><input type="submit" value="Register"></p>
                </form>
</body>

</html>

