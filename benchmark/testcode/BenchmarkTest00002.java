package org.owasp.benchmark.testcode;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.sql.*;

@WebServlet(value="/sqli-00002")
public class BenchmarkTest00002 extends HttpServlet {

    private static final long serialVersionUID = 1L;

    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doPost(request, response);
    }

    @Override
    public void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        response.setContentType("text/html;charset=UTF-8");

        String param = request.getParameter("username");

        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/benchmark", "root", "password");
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(
                "SELECT * FROM users WHERE username = '" + param + "' AND active = 1");

            while (rs.next()) {
                response.getWriter().println(rs.getString("email"));
            }

            rs.close();
            stmt.close();
            conn.close();
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }
}
