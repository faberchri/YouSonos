import React from "react";
import {cancelSearch, SearchResult, searchResults, searchTracks, Track} from "./api";
import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import SearchResultList from "./SearchResultList";
import SearchInputField from "./SearchInputField";

interface State {
    searchString: string;
    indicateError: boolean,
    indicateSearchRunning: boolean,
    searchHitCount: number
}

const styles = (theme: Theme) => createStyles({
    root: {
        display: 'flex',
        flexFlow: 'column',
    }
});

interface Props extends WithStyles<typeof styles> {
}

class SearchControl extends React.Component<Props, State> {

    subject = new Subject<string>();

    constructor(props: Props) {
        super(props);
        this.state = SearchControl.getInitialState();
        this.subject
            .pipe(debounce(() => timer(500)))
            .subscribe((url) => searchTracks(url));
    }

    static getInitialState(): State {
        return {
            searchString: '',
            indicateError: false,
            indicateSearchRunning: false,
            searchHitCount: 0,
        };
    }

    componentDidMount() {
        searchResults(this.setSearchResults);
    }

    setSearchResults = (searchResult: SearchResult) =>{
        if (searchResult.search_string === this.state.searchString) {
            const searchHitCount = searchResult.results.length;
            this.setState({
                searchString: this.state.searchString,
                indicateError: this.state.indicateError
                    || searchResult.has_error
                    || (this.state.searchHitCount + searchHitCount) === 0 && searchResult.search_completed,
                indicateSearchRunning: !searchResult.search_completed,
                searchHitCount: searchHitCount,
            });
        }
    };

    runSearch = (searchString: string) => {
        if (searchString.length === 0) {
            this.cancelSearch();
        } else {
            this.setState({
                searchString: searchString,
                indicateError: false,
                indicateSearchRunning: true,
                searchHitCount: 0,
            });
            this.subject.next(searchString);
        }
    };

    cancelSearch = () => {
        this.setState(SearchControl.getInitialState());
        cancelSearch()
    };

    render() {

        const {classes} = this.props;

        return (
            <div className={classes.root} >
                <SearchInputField
                    searchString={this.state.searchString}
                    onValueChange={this.runSearch}
                    onFieldReset={this.cancelSearch}
                    indicateError={this.state.indicateError}
                    indicateSearchRunning={this.state.indicateSearchRunning} />
                <SearchResultList/>
            </div>
        );
    }
}

export default withStyles(styles)(SearchControl);
