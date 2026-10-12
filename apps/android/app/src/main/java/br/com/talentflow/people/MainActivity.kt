package br.com.talentflow.people

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import br.com.talentflow.people.data.AppViewModel
import br.com.talentflow.people.ui.TalentFlowRoot
import br.com.talentflow.people.ui.theme.TalentFlowTheme

class MainActivity : ComponentActivity() {
    private val viewModel: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { TalentFlowTheme { TalentFlowRoot(viewModel) } }
    }
}
