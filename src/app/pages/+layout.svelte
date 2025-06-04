<script>
	import '@evidence-dev/tailwind/fonts.css';
	import '../app.css';
	import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
	export let data;
</script>

<EvidenceDefaultLayout {data} title="Contratos de Madrid" builtWithEvidence=false homePageName="Buscador de Empresas" fullWidth=true neverShowQueries=true githubRepo="https://github.com/franloza/contratosdemadrid" >
	<slot slot="content" />
</EvidenceDefaultLayout>